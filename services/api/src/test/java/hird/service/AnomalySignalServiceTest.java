package hird.service;

import hird.dto.AnomalySignalResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.model.AnomalySignal;
import hird.repository.AnomalySignalRepository;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class AnomalySignalServiceTest {

    @Test
    void returnsAnomaliesWhenDataExists() {
        AnomalySignalRepository repo = mock(AnomalySignalRepository.class);

        AnomalySignal row = new AnomalySignal(
                UUID.randomUUID(),
                "Kelowna",
                "price",
                LocalDate.of(2025,1,1),
                0.8,
                true
        );

        when(repo.findByCityAndTargetOrderByDetectDateAsc("Kelowna", "price"))
                .thenReturn(List.of(row));

        AnomalySignalService service = new AnomalySignalService(repo);

        AnomalySignalResponse resp =
                service.retrieveAnomalies("Kelowna", "price");

        assertEquals("Kelowna", resp.city());
        assertEquals("price", resp.target());
        assertEquals(1, resp.signals().size());
    }

    @Test
    void throwsNotFound() {
        AnomalySignalRepository repo = mock(AnomalySignalRepository.class);
        when(repo.findByCityAndTargetOrderByDetectDateAsc("Kelowna", "price"))
                .thenReturn(List.of());

        AnomalySignalService service = new AnomalySignalService(repo);

        assertThrows(ResourceNotFoundException.class,
                () -> service.retrieveAnomalies("Kelowna", "price")
        );
    }
}
