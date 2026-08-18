import React from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

// Recharts SVG fills resolve CSS variables inconsistently across browsers,
// so band colors are literal values mirroring the theme tokens.
const ACCENT = '#14b8a6';
const BAND_LOW = 'rgba(22, 163, 74, 0.06)';
const BAND_MOD = 'rgba(245, 158, 11, 0.06)';
const BAND_HIGH = 'rgba(220, 38, 38, 0.06)';

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function RiskTrendChart({ history, height = 240 }) {
  const data = [...(history || [])]
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    .map((row) => ({
      date: formatDate(row.created_at),
      risk: Math.round(row.risk_probability * 1000) / 10
    }));

  if (data.length < 2) return null;

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <defs>
            <linearGradient id="diaRiskFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT} stopOpacity={0.25} />
              <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
            </linearGradient>
          </defs>
          <ReferenceArea y1={0} y2={35} fill={BAND_LOW} strokeOpacity={0} />
          <ReferenceArea y1={35} y2={65} fill={BAND_MOD} strokeOpacity={0} />
          <ReferenceArea y1={65} y2={100} fill={BAND_HIGH} strokeOpacity={0} />
          <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: 'currentColor', opacity: 0.6 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 11, fill: 'currentColor', opacity: 0.6 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value) => [`${value}%`, 'Risk probability']}
            contentStyle={{
              borderRadius: 8,
              border: '1px solid rgba(128,128,128,0.3)',
              fontSize: '0.8rem'
            }}
          />
          <Area
            type="monotone"
            dataKey="risk"
            stroke={ACCENT}
            strokeWidth={2}
            fill="url(#diaRiskFill)"
            dot={{ r: 3, fill: ACCENT, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
