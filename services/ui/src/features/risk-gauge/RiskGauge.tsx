import { AlertCircle } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import RiskGaugeHeader from "./RiskGaugeHeader";
import Frame from "../../ui/Frame";

function RiskGauge() {
  const riskScore = 62;

  const riskData = [
    { name: "risk", value: riskScore, fill: "#ef4444" },
    { name: "remainder", value: 100 - riskScore, fill: "#262626" },
  ];

  return (
    <Frame className="col-span-12 lg:col-span-4 flex flex-col">
      <RiskGaugeHeader />
      <div className="flex gap-4 items-center">
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

        <div className="flex-1 text-sm divide-y divide-neutral-700">
          <div className="flex items-center justify-between py-4">
            <span className="opacity-80">Affordability</span>
            <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800 text-neutral-200">
              Tight
            </span>
          </div>

          <div className="flex items-center justify-between py-4">
            <span className="opacity-80">Price-to-Rent</span>
            <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800 text-neutral-200">
              Elevated
            </span>
          </div>

          <div className="flex items-center justify-between py-4">
            <span className="opacity-80">Inventory</span>
            <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800 text-neutral-200">
              Low
            </span>
          </div>
        </div>
      </div>

      <div className="mt-auto text-xs flex items-start gap-2 opacity-70">
        <AlertCircle className="size-4" />
        <p>
          Interpretation: 0=low risk, 100=high risk. Composite for illustration.
        </p>
      </div>
    </Frame>
  );
}

export default RiskGauge;
