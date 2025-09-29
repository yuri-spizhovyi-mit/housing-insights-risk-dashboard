import { useQueryClient } from "@tanstack/react-query";
import Button from "../../ui/Button";
import { TrendingUp } from "lucide-react";

function PredictTrigger() {
  const queryClient = useQueryClient();

  function runPrediction() {
    queryClient.invalidateQueries();
  }

  return (
    <Button
      onClick={runPrediction}
      leftIcon={<TrendingUp className="w-4 h-4" />}
      className="ml-4 px-6 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold"
    >
      Predict
    </Button>
  );
}

export default PredictTrigger;
