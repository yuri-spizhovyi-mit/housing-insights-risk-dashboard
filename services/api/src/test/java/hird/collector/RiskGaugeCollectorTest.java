package hird.collector;

import hird.model.RiskGauge;
import hird.service.collector.RiskGaugeIndexCollector;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;


class RiskGaugeCollectorTest {

    @Test
    void collectsLatestValuePerRiskType() {
        List<RiskGauge> rows = List.of(
            new RiskGauge(UUID.randomUUID(), "Toronto", "POS", 0.24, LocalDate.now()),
            new RiskGauge(UUID.randomUUID(), "Vancouver", "NEG", 0.84, LocalDate.now()),
            new RiskGauge(UUID.randomUUID(), "London", "POS", 0.30, LocalDate.now())
        );

        Map<String, Double> index = RiskGaugeIndexCollector.collect(rows);

        assertEquals(2, index.size());
        assertEquals(0.30, index.get("POS"));
        assertEquals(0.84, index.get("NEG"));
    }

}

