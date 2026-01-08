import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { formatElapsedTime } from './date';

describe('formatElapsedTime', () => {
  beforeEach(() => {
    // Mock current time to 2026-01-08T10:00:00Z for consistent testing
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-08T10:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('when completedAt is provided (fixed duration)', () => {
    it('should format elapsed time under 1 minute as "Xs"', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T10:00:30Z'; // 30 seconds later

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('30s');
    });

    it('should format elapsed time between 1 minute and 1 hour as "Xm Ys"', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T10:03:25Z'; // 3 minutes 25 seconds later

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('3m 25s');
    });

    it('should format elapsed time over 1 hour as "Xh Ym"', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T11:15:30Z'; // 1 hour 15 minutes 30 seconds later

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('1h 15m');
    });

    it('should format exactly 1 hour as "1h" without minutes', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T11:00:00Z'; // exactly 1 hour later

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('1h');
    });

    it('should format exactly 1 minute as "1m" without seconds', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T10:01:00Z'; // exactly 1 minute later

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('1m');
    });
  });

  describe('when completedAt is not provided (ongoing task)', () => {
    it('should calculate elapsed time from startedAt to current time', () => {
      // RED Phase: Function doesn't exist yet
      // Current time is mocked to 2026-01-08T10:00:00Z
      const startedAt = '2026-01-08T09:56:35Z'; // 3 minutes 25 seconds before current time

      const result = formatElapsedTime(startedAt);

      expect(result).toBe('3m 25s');
    });

    it('should handle ongoing task under 1 minute', () => {
      // RED Phase: Function doesn't exist yet
      // Current time is mocked to 2026-01-08T10:00:00Z
      const startedAt = '2026-01-08T09:59:45Z'; // 15 seconds before current time

      const result = formatElapsedTime(startedAt);

      expect(result).toBe('15s');
    });

    it('should handle ongoing task over 1 hour', () => {
      // RED Phase: Function doesn't exist yet
      // Current time is mocked to 2026-01-08T10:00:00Z
      const startedAt = '2026-01-08T08:30:00Z'; // 1 hour 30 minutes before current time

      const result = formatElapsedTime(startedAt);

      expect(result).toBe('1h 30m');
    });
  });

  describe('edge cases', () => {
    it('should handle very long durations (multi-hour)', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T15:45:30Z'; // 5 hours 45 minutes 30 seconds

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('5h 45m');
    });

    it('should handle zero seconds (instant completion)', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00Z';
      const completedAt = '2026-01-08T10:00:00Z'; // same time

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('0s');
    });

    it('should handle timestamps without Z suffix (assume UTC)', () => {
      // RED Phase: Function doesn't exist yet
      const startedAt = '2026-01-08T10:00:00';
      const completedAt = '2026-01-08T10:01:30';

      const result = formatElapsedTime(startedAt, completedAt);

      expect(result).toBe('1m 30s');
    });
  });
});
