package hird.repository;

import hird.model.AnomalySignal;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface AnomalySignalRepository extends JpaRepository<AnomalySignal, UUID> {

    List<AnomalySignal> findByCityAndTargetOrderByDetectDateAsc(String city, String target);
}
