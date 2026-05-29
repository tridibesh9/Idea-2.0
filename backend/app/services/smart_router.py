import uuid
import logging
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.complaint import Complaint

logger = logging.getLogger("smart_router")

CATEGORY_TO_DEPARTMENT = {
    "billing": "Billing",
    "refund": "Billing",
    "product_defect": "Technical",
    "account_access": "Technical",
    "service_delay": "Customer Support",
    "delivery": "Customer Support",
}

async def route_complaint(complaint: Complaint, db: AsyncSession) -> uuid.UUID | None:
    """
    Automatically routes a complaint to an agent based on their department
    matching the complaint category, and balances load by choosing the agent
    with the minimum number of currently open/active complaints.
    """
    category = complaint.category or "general"
    target_dept = CATEGORY_TO_DEPARTMENT.get(category, "Customer Support")
    
    logger.info(f"Routing complaint {complaint.id} (Category: {category}) -> Dept: {target_dept}")
    
    try:
        # Get all agents in the target department
        result = await db.execute(
            select(Agent).where(Agent.department == target_dept)
        )
        agents = result.scalars().all()
        
        # If no agents in the department, fall back to all Customer Support agents, or just all agents
        if not agents:
            logger.warning(f"No agents found in department {target_dept}, falling back to Customer Support")
            result = await db.execute(
                select(Agent).where(Agent.department == "Customer Support")
            )
            agents = result.scalars().all()
            
            if not agents:
                logger.warning("No Customer Support agents found, falling back to all available agents")
                result = await db.execute(select(Agent))
                agents = result.scalars().all()
                
                if not agents:
                    logger.error("No agents seeded in the database. Cannot auto-assign.")
                    return None

        # Find the workloads of these agents (count of open complaints: status not in ('resolved', 'closed'))
        agent_ids = [agent.id for agent in agents]
        
        # Query count of active complaints per agent
        workload_query = (
            select(Complaint.assigned_agent_id, func.count(Complaint.id).label("active_count"))
            .where(
                and_(
                    Complaint.assigned_agent_id.in_(agent_ids),
                    Complaint.status.notin_(["resolved", "closed"])
                )
            )
            .group_by(Complaint.assigned_agent_id)
        )
        workload_result = await db.execute(workload_query)
        workload_map = {row.assigned_agent_id: row.active_count for row in workload_result.all()}
        
        # Determine the agent with the minimum workload
        min_load = float("inf")
        selected_agent = None
        
        # Iterate over all agents to default missing workloads to 0
        for agent in agents:
            load = workload_map.get(agent.id, 0)
            if load < min_load:
                min_load = load
                selected_agent = agent
                
        if selected_agent:
            complaint.assigned_agent_id = selected_agent.id
            # Also update the status from new to open since an agent has been assigned
            if complaint.status == "new":
                complaint.status = "open"
            logger.info(f"Assigned complaint {complaint.id} to agent {selected_agent.name} (Active load: {min_load})")
            return selected_agent.id
            
    except Exception as e:
        logger.error(f"Error during smart routing: {e}")
        
    return None
