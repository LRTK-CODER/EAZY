import { formatDistanceToNow as baseFn, differenceInSeconds } from 'date-fns';

/**
 * 날짜를 UTC로 파싱하여 현재 시간과의 차이를 표시
 *
 * @param date - 날짜 문자열 또는 Date 객체
 * @param options - date-fns formatDistanceToNow 옵션
 * @returns 상대 시간 문자열 (예: "2 hours ago")
 */
export function formatDistanceToNow(
  date: string | Date | null | undefined,
  options?: { addSuffix?: boolean }
): string {
  // null/undefined 체크
  if (!date) {
    return 'Unknown';
  }

  // Date 객체면 그대로 사용
  if (date instanceof Date) {
    return baseFn(date, options);
  }

  // 문자열인 경우 UTC 파싱
  // timezone 정보가 없으면 'Z' 추가 (UTC 명시)
  const utcDate = date.endsWith('Z') || date.includes('+')
    ? new Date(date)
    : new Date(date + 'Z');

  return baseFn(utcDate, options);
}

/**
 * Parse ISO 8601 timestamp string to Date object (UTC assumed)
 *
 * @param timestamp - ISO 8601 timestamp string (e.g., "2026-01-08T10:00:00Z")
 * @returns Date object
 */
function parseTimestamp(timestamp: string): Date {
  // If no timezone info, assume UTC by adding 'Z'
  const normalizedTimestamp = timestamp.endsWith('Z') || timestamp.includes('+')
    ? timestamp
    : timestamp + 'Z';

  return new Date(normalizedTimestamp);
}

/**
 * Format elapsed time between two timestamps or from startedAt to now
 *
 * @param startedAt - ISO 8601 timestamp when task started
 * @param completedAt - Optional ISO 8601 timestamp when task completed (uses current time if not provided)
 * @returns Formatted elapsed time string
 *   - Under 1 minute: "Xs" (e.g., "45s")
 *   - 1 minute to 1 hour: "Xm Ys" (e.g., "3m 25s")
 *   - Over 1 hour: "Xh Ym" (e.g., "1h 15m")
 *
 * @example
 * formatElapsedTime('2026-01-08T10:00:00Z', '2026-01-08T10:00:30Z') // "30s"
 * formatElapsedTime('2026-01-08T10:00:00Z', '2026-01-08T10:03:25Z') // "3m 25s"
 * formatElapsedTime('2026-01-08T10:00:00Z', '2026-01-08T11:15:30Z') // "1h 15m"
 * formatElapsedTime('2026-01-08T10:00:00Z') // calculates from now
 */
export function formatElapsedTime(startedAt: string, completedAt?: string): string {
  const startDate = parseTimestamp(startedAt);
  const endDate = completedAt ? parseTimestamp(completedAt) : new Date();

  // Calculate total elapsed seconds
  const totalSeconds = differenceInSeconds(endDate, startDate);

  // Handle edge case: 0 seconds
  if (totalSeconds === 0) {
    return '0s';
  }

  // Calculate hours, minutes, seconds
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  // Format based on duration magnitude
  if (hours > 0) {
    // Over 1 hour: "Xh Ym" format
    if (minutes === 0) {
      return `${hours}h`;
    }
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    // 1 minute to 1 hour: "Xm Ys" format
    if (seconds === 0) {
      return `${minutes}m`;
    }
    return `${minutes}m ${seconds}s`;
  } else {
    // Under 1 minute: "Xs" format
    return `${seconds}s`;
  }
}
