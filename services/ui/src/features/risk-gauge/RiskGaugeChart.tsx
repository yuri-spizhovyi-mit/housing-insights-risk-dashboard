import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

interface RiskGaugeChartProps {
  riskScore: number;
}

function RiskGaugeChart({ riskScore }: RiskGaugeChartProps) {
  const riskData = [
    { name: "risk", value: riskScore, fill: "#ef4444" },
    { name: "remainder", value: 100 - riskScore, fill: "#262626" },
  ];

  return (
    <div className="flex-[0.5] h-full w-full flex items-center justify-center">
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={riskData}
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="80%"
            startAngle={90}
            endAngle={-270}
            paddingAngle={0}
            dataKey="value"
          >
            {riskData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>

          <text
            x="50%"
            y="50%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-sm xl:text-lg font-semibold"
            fill="#e7e1cc"
          >
            {riskScore}%
          </text>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default RiskGaugeChart;
