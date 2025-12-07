package hird.service.collector;

import hird.model.RiskGauge;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class RiskGaugeIndexCollector {

    private RiskGaugeIndexCollector() {}

    public static Map<String, Double> collect(List<RiskGauge> rows) {
        Map<String, Double> index = new HashMap<>();

        for (RiskGauge row : rows) {
            index.put(row.getRiskType(), row.getRiskValue());
        }

        return index;
    }
}
