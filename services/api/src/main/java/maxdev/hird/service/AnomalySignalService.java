package maxdev.hird.service;


import maxdev.hird.domain.exceptions.ResourceNotFoundException;
import maxdev.hird.dto.AnomalySignalItemResponse;
import maxdev.hird.dto.AnomalySignalResponse;
import maxdev.hird.model.AnomalySignal;
import maxdev.hird.repository.AnomalySignalRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AnomalySignalService {

    private final AnomalySignalRepository anomalySignalRepository;

    public AnomalySignalService(AnomalySignalRepository anomalySignalRepository) {
        this.anomalySignalRepository = anomalySignalRepository;
    }

    @Cacheable(
            value = "ANOMALIES_CACHE",
            key = "#city.toLowerCase() + ':' + #target.toLowerCase()"
    )
    public AnomalySignalResponse retrieveAnomalies(String city, String target) {
        List<AnomalySignal> rows =
                anomalySignalRepository.findByCityIgnoreCaseAndTargetIgnoreCaseOrderByDetectDateAsc(city, target);

        if (rows.isEmpty()) {
            throw new ResourceNotFoundException("No anomalies for " + city + ", target: " + target);
        }

        return new AnomalySignalResponse(city, target, toItems(rows));
    }

    private List<AnomalySignalItemResponse> toItems(List<AnomalySignal> rows) {
        return rows.stream()
                .map(this::toItem)
                .toList();
    }

    private AnomalySignalItemResponse toItem(AnomalySignal r) {
        return new AnomalySignalItemResponse(
                r.getDetectDate().toString(),
                r.getAnomalyScore(),
                r.getIsAnomaly()
        );
    }
}
