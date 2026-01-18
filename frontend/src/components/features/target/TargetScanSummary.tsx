import { useMemo } from 'react';
import { Clock, Loader2, Check, X, Ban, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TaskStatus, type Task } from '@/types/task';
import { formatElapsedTime, formatDistanceToNow } from '@/utils/date';

interface TargetScanSummaryProps {
  task?: Task;
  onClick?: () => void;
  isLoading?: boolean;
  className?: string;
}

const STATUS_CONFIG = {
  [TaskStatus.PENDING]: {
    icon: Clock,
    iconClassName: '',
    className: 'text-amber-600 dark:text-amber-400',
    label: 'Pending',
  },
  [TaskStatus.RUNNING]: {
    icon: Loader2,
    iconClassName: 'animate-spin',
    className: 'text-blue-600 dark:text-blue-400',
    label: 'Running',
  },
  [TaskStatus.COMPLETED]: {
    icon: Check,
    iconClassName: '',
    className: 'text-green-600 dark:text-green-400',
    label: 'Completed',
  },
  [TaskStatus.FAILED]: {
    icon: X,
    iconClassName: '',
    className: 'text-red-600 dark:text-red-400',
    label: 'Failed',
  },
  [TaskStatus.CANCELLED]: {
    icon: Ban,
    iconClassName: '',
    className: 'text-muted-foreground',
    label: 'Cancelled',
  },
} as const;

export function TargetScanSummary({
  task,
  onClick,
  isLoading = false,
  className,
}: TargetScanSummaryProps) {
  const display = useMemo(() => {
    if (!task) {
      return {
        icon: Minus,
        iconClassName: '',
        className: 'text-muted-foreground',
        text: '-',
        ariaLabel: 'No scan',
      };
    }

    const config = STATUS_CONFIG[task.status];
    const isActive = task.status === TaskStatus.PENDING || task.status === TaskStatus.RUNNING;

    let text: string;
    if (isActive && task.started_at) {
      text = formatElapsedTime(task.started_at);
    } else if (task.status === TaskStatus.COMPLETED && task.completed_at) {
      text = formatDistanceToNow(task.completed_at, { addSuffix: true });
    } else {
      text = config.label;
    }

    return {
      icon: config.icon,
      iconClassName: config.iconClassName,
      className: config.className,
      text,
      ariaLabel: `Scan status: ${config.label}`,
    };
  }, [task]);

  if (isLoading) {
    return (
      <span className={cn('text-sm text-muted-foreground', className)}>
        ...
      </span>
    );
  }

  const Icon = display.icon;

  const content = (
    <span
      role="status"
      aria-label={display.ariaLabel}
      className={cn(
        'inline-flex items-center gap-1 text-sm font-medium',
        display.className,
        className
      )}
    >
      <Icon
        className={cn('h-3.5 w-3.5', display.iconClassName)}
        aria-hidden="true"
      />
      <span>{display.text}</span>
    </span>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={cn(
          'inline-flex items-center gap-1 text-sm font-medium',
          'cursor-pointer rounded-md px-1.5 py-0.5 -mx-1.5 -my-0.5',
          'hover:bg-accent/50',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'transition-colors duration-150',
          display.className,
          className
        )}
      >
        <span role="status" aria-label={display.ariaLabel} className="contents">
          <Icon
            className={cn('h-3.5 w-3.5', display.iconClassName)}
            aria-hidden="true"
          />
          <span>{display.text}</span>
        </span>
      </button>
    );
  }

  return content;
}
