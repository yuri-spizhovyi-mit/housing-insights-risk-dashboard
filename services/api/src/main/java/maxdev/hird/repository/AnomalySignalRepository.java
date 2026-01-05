package maxdev.hird.repository;


import maxdev.hird.model.AnomalySignal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface AnomalySignalRepository extends JpaRepository<AnomalySignal, UUID> {
    List<AnomalySignal> findByCityIgnoreCaseAndTargetIgnoreCaseOrderByDetectDateAsc(String city, String target);
    List<AnomalySignal> findTop3ByCityIgnoreCaseAndIsAnomalyTrueOrderByDetectDateDesc(String city);
}

