package maxdev.hird.service;

import maxdev.hird.domain.util.ReportRenderer;
import maxdev.hird.domain.util.ReportRendererImpl;
import maxdev.hird.model.AnomalySignal;
import maxdev.hird.model.ModelPrediction;
import maxdev.hird.model.RiskGauge;
import maxdev.hird.repository.AnomalySignalRepository;
import maxdev.hird.repository.ModelPredictionRepository;
import maxdev.hird.repository.RiskGaugeRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ReportService {

    private static final String TARGET_PRICE = "price";

    private final ModelPredictionRepository predictionRepository;
    private final RiskGaugeRepository riskGaugeRepository;
    private final AnomalySignalRepository anomalySignalRepository;
    private final ReportRenderer reportRenderer;

    public ReportService(
            ModelPredictionRepository predictionRepository,
            RiskGaugeRepository riskGaugeRepository,
            AnomalySignalRepository anomalySignalRepository,
            ReportRendererImpl reportRenderer
    ) {
        this.predictionRepository = predictionRepository;
        this.riskGaugeRepository = riskGaugeRepository;
        this.anomalySignalRepository = anomalySignalRepository;
        this.reportRenderer = reportRenderer;
    }

    @Cacheable(
            value = "REPORT_CACHE",
            key = "#city.toLowerCase()"
    )
    public byte[] buildCityReport(String city) {
        List<ModelPrediction> forecastRows =
                predictionRepository.findByCityIgnoreCaseAndTargetIgnoreCaseOrderByPredictDateAsc(city, TARGET_PRICE);

        List<RiskGauge> riskRows =
                riskGaugeRepository.findByCityIgnoreCaseOrderByPredictDateDesc(city);

        List<AnomalySignal> anomalyRows =
                anomalySignalRepository.findTop3ByCityIgnoreCaseAndIsAnomalyTrueOrderByDetectDateDesc(city);

        return reportRenderer.render(city, forecastRows, riskRows, anomalyRows);
    }
}
