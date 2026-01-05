package maxdev.hird.repository;


import maxdev.hird.model.RiskGauge;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface RiskGaugeRepository extends JpaRepository<RiskGauge, UUID> {
    List<RiskGauge> findByCityIgnoreCaseOrderByPredictDateDesc(String city);
}

