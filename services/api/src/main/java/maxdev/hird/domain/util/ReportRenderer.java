package maxdev.hird.domain.util;

import maxdev.hird.model.AnomalySignal;
import maxdev.hird.model.ModelPrediction;
import maxdev.hird.model.RiskGauge;

import java.util.List;

@FunctionalInterface
public interface ReportRenderer {
    byte[] render(
            String city,
            List<ModelPrediction> forecastRows,
            List<RiskGauge> riskRows,
            List<AnomalySignal> anomalyRows
    );
}

