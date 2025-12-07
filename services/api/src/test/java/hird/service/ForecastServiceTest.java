package hird.service;

import hird.dto.ForecastRequest;
import hird.dto.ForecastResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.model.ModelPrediction;
import hird.repository.ModelPredictionRepository;
import org.junit.jupiter.api.Test;
import org.springframework.data.jpa.domain.Specification;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ForecastServiceTest {

    @Test
    void returnsForecastWhenDataExists() {
        ModelPredictionRepository repo = mock(ModelPredictionRepository.class);

        ModelPrediction row = new ModelPrediction();
        row.setPredictDate(LocalDate.of(2025, 1, 1));
        row.setYhat(200.0);
        row.setYhatLower(150.0);
        row.setYhatUpper(250.0);

        when(repo.findAll(any(Specification.class))).thenReturn(List.of(row));

        ForecastService service = new ForecastService(repo);

        ForecastRequest req = new ForecastRequest(
                "Kelowna",
                "price",
                "1y",
                0,
                1500,
                "Any",
                "2",
                "3"
        );

        ForecastResponse response = service.retrieveForecast(req);

        assertEquals(1, response.data().size());
    }

    @Test
    void throwsNotFound() {
        ModelPredictionRepository repo = mock(ModelPredictionRepository.class);
        when(repo.findAll(any(Specification.class))).thenReturn(List.of());

        ForecastService service = new ForecastService(repo);

        ForecastRequest req = new ForecastRequest(
                "Kelowna",
                "price",
                "1y",
                0,
                2000,
                "Any",
                "Any",
                "Any"
        );

        assertThrows(ResourceNotFoundException.class,
                () -> service.retrieveForecast(req)
        );
    }
}
