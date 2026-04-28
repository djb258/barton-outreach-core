export const EMAIL_DELIVERABILITY_CONFIG = {
  warmup: {
    bounce_rate_threshold_percent: 5,
    warmup_caps: {
      1: 20,
      2: 40,
      3: 80,
      4: 150,
      5: 250,
    } as Record<number, number>,
  },
  reply_to: 'Dave Barton <dave@svg.agency>',
} as const;

export function bounceRatePercent(sentToday: number, bounceCount24h: number): number {
  if (sentToday <= 0) return 0;
  return (bounceCount24h / sentToday) * 100;
}

export function isBounceRateHealthy(sentToday: number, bounceCount24h: number): boolean {
  return bounceRatePercent(sentToday, bounceCount24h) <= EMAIL_DELIVERABILITY_CONFIG.warmup.bounce_rate_threshold_percent;
}

export function nextWarmupCap(warmupWeek: number): number {
  return EMAIL_DELIVERABILITY_CONFIG.warmup.warmup_caps[warmupWeek] ?? 250;
}
