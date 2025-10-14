export type Indicator = {
  name: string;
  status: "Tight" | "Elevated" | "Low";
};

export type CityInsight = {
  city: string;
  date: string;
  score: number;
  breakdown: Indicator[];
};
