package hird.collector;

import hird.dto.ForecastPointResponse;
import hird.model.ModelPrediction;
import hird.service.collector.ForecastPointCollector;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class ForecastPointCollectorTest {

    @Test
    void keepsUniqueDatesAndSortsThem() {
        ModelPrediction jan1a = prediction("2025-01-01", 100.0, 90, 110);
        ModelPrediction jan1b = prediction("2025-01-01", 200.0, 180, 220);
        ModelPrediction feb1  = prediction("2025-02-01", 150.0, 130, 170);

        List<ForecastPointResponse> result =
                ForecastPointCollector.collect(List.of(jan1a, jan1b, feb1));

        assertEquals(2, result.size());

        assertEquals("2025-01-01", result.get(0).date());
        assertEquals(100.0, result.get(0).value());
        assertEquals(90.0, result.get(0).lower());
        assertEquals(110.0, result.get(0).upper());

        assertEquals("2025-02-01", result.get(1).date());
        assertEquals(150.0, result.get(1).value());
    }


    public static ModelPrediction prediction(String date, double yhat, double lower, double upper) {
        ModelPrediction p = new ModelPrediction();
        p.setPredictDate(LocalDate.parse(date));
        p.setYhat(yhat);
        p.setYhatLower(lower);
        p.setYhatUpper(upper);
        return p;
    }
}
