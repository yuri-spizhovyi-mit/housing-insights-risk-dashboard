package hird.service;

import hird.dto.AnomalySignalResponse;
import hird.dto.AnomalySignalItemResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.repository.AnomalySignalRepository;
import hird.service.collector.AnomalySignalCollector;
import hird.model.AnomalySignal;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AnomalySignalService {

    private final AnomalySignalRepository repo;

    public AnomalySignalService(AnomalySignalRepository repo) {
        this.repo = repo;
    }

    public AnomalySignalResponse retrieveAnomalies(String city, String target) {

        List<AnomalySignal> rows =
                repo.findByCityAndTargetOrderByDetectDateAsc(city, target);

        if (rows.isEmpty())
            throw new ResourceNotFoundException(
                    "No anomalies for " + city + ", target:" + target
            );

        List<AnomalySignalItemResponse> items =
                AnomalySignalCollector.collect(rows);

        return new AnomalySignalResponse(city, target, items);
    }
}
