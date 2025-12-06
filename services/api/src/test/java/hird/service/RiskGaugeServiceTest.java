package hird.service;

import hird.exceptions.ResourceNotFoundException;
import hird.repository.RiskGaugeRepository;
import hird.dto.RiskGaugeResponse;
import hird.model.RiskGauge;
import org.junit.jupiter.api.Test;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class RiskGaugeServiceTest {

    @Test
    void returnsRiskGaugeWhenDataExists() {
        RiskGaugeRepository repo = mock(RiskGaugeRepository.class);

        RiskGauge row1 = new RiskGauge(
                UUID.randomUUID(), "Kelowna", "affordability",
                0.75, LocalDate.of(2025, 1, 1)
        );

        when(repo.findByCityOrderByPredictDateDesc("Kelowna"))
                .thenReturn(List.of(row1));

        RiskGaugeService service = new RiskGaugeService(repo);

        RiskGaugeResponse response = service.retrieveRiskGaugeData("Kelowna");

        assertEquals("Kelowna", response.city());
        assertEquals("2025-01-01", response.date());
        assertNotNull(response.breakdown());
        assertEquals(3, response.breakdown().size());
    }

    @Test
    public void throwsNotFound(){
        RiskGaugeRepository repository = mock(RiskGaugeRepository.class);
        when(repository.findByCityOrderByPredictDateDesc("Kelowna")).thenReturn(List.of());

        RiskGaugeService service = new RiskGaugeService(repository);

        assertThrows(ResourceNotFoundException.class,
                () -> service.retrieveRiskGaugeData("Kelowna")
        );
    }
}
