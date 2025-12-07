package hird.service.collector;

import hird.dto.AnomalySignalItemResponse;
import hird.model.AnomalySignal;

import java.util.List;

public final class AnomalySignalCollector {

    private AnomalySignalCollector() {}

    public static List<AnomalySignalItemResponse> collect(List<AnomalySignal> rows) {
        return rows.stream()
                .map(r -> new AnomalySignalItemResponse(
                        r.getDetectDate().toString(),
                        r.getAnomalyScore(),
                        r.getIsAnomaly()
                ))
                .toList();
    }
}
