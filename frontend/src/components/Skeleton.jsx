import clsx from 'clsx';

export function SkeletonLine({ className }) {
  return (
    <div className={clsx('animate-pulse bg-gray-200 dark:bg-gray-700 rounded', className)} />
  );
}

export function SkeletonCard({ lines = 3 }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4 space-y-3">
      <SkeletonLine className="h-4 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine key={i} className={`h-3 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`} />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 6 }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 overflow-hidden">
      <div className="bg-gray-50 dark:bg-gray-700/50 p-3">
        <SkeletonLine className="h-4 w-1/4" />
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 p-3 border-t dark:border-gray-700">
          {Array.from({ length: cols }).map((_, c) => (
            <SkeletonLine key={c} className={`h-3 flex-1 ${c === 0 ? 'max-w-[80px]' : ''}`} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonKPIs({ count = 5 }) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 lg:grid-cols-${count} gap-4`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <SkeletonLine className="h-10 w-10 rounded-lg" />
            <div className="space-y-2 flex-1">
              <SkeletonLine className="h-6 w-16" />
              <SkeletonLine className="h-3 w-24" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
