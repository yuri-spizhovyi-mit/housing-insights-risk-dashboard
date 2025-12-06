package hird.collector;

import hird.dto.AnomalySignalItemResponse;
import hird.model.AnomalySignal;
import hird.service.collector.AnomalySignalCollector;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class AnomalySignalCollectorTest {

    @Test
    void mapsEntitiesToResponses() {
        AnomalySignal a = new AnomalySignal(
                UUID.randomUUID(),
                "Kelowna",
                "price",
                LocalDate.of(2025,1,1),
                0.95,
                true
        );

        List<AnomalySignalItemResponse> result =
                AnomalySignalCollector.collect(List.of(a));

        assertEquals(1, result.size());

        var r = result.get(0);
        assertEquals("2025-01-01", r.date());
        assertEquals(0.95, r.score());
        assertTrue(r.isAnomaly());
    }
}
