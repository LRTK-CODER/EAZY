import { formatDistanceToNow as baseFn } from 'date-fns';

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
