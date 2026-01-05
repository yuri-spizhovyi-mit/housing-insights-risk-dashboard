package maxdev.hird.service;

import maxdev.hird.domain.exceptions.ResourceNotFoundException;
import maxdev.hird.domain.util.HorizonParser;
import maxdev.hird.dto.ForecastPointResponse;
import maxdev.hird.dto.ForecastRequest;
import maxdev.hird.dto.ForecastResponse;
import maxdev.hird.model.ModelPrediction;
import maxdev.hird.repository.ModelPredictionRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class ForecastService {

    private final ModelPredictionRepository forecastRepository;

    public ForecastService(ModelPredictionRepository forecastRepository) {
        this.forecastRepository = forecastRepository;
    }

    @Cacheable(
            value = "FORECAST_CACHE",
            key = "#forecastRequest.city.toLowerCase() + ':' + " +
                    "#forecastRequest.target.toLowerCase() + ':' + " +
                    "#forecastRequest.horizon.toLowerCase() + ':' + " +
                    "#forecastRequest.modelName.toLowerCase()"
    )
    public ForecastResponse retrieveForecast(ForecastRequest forecastRequest) {
        int months = HorizonParser.toMonths(forecastRequest.horizon().toLowerCase());
        List<ModelPrediction> rows = forecastRepository.findForecastSeries(forecastRequest, months);

        if (rows.isEmpty()) {
            throw new ResourceNotFoundException(
                    "No data for %s, %s, %s, model=%s".formatted(
                            forecastRequest.city(),
                            forecastRequest.target(),
                            forecastRequest.horizon(),
                            forecastRequest.modelName()
                    )
            );
        }

        List<ForecastPointResponse> full = rows.stream().map(this::toPoint).toList();
        List<ForecastPointResponse> sampled = applyHorizonSampling(full, months);

        return new ForecastResponse(
                forecastRequest.city(),
                forecastRequest.target(),
                months,
                sampled
        );
    }

    private ForecastPointResponse toPoint(ModelPrediction row) {
        return new ForecastPointResponse(
                row.getPredictDate().toString(),
                row.getYhat(),
                row.getYhatLower(),
                row.getYhatUpper()
        );
    }

    private List<ForecastPointResponse> applyHorizonSampling(List<ForecastPointResponse> full, int months) {
        if (months == 12) return full;

        if (months == 24) {
            List<ForecastPointResponse> sampled = new ArrayList<>();
            for (int i = 0; i < full.size(); i += 2) sampled.add(full.get(i));
            return sampled;
        }

        if (months >= 60) {
            int step = Math.max(1, full.size() / 12);
            List<ForecastPointResponse> sampled = new ArrayList<>();
            for (int i = 0; i < full.size() && sampled.size() < 12; i += step) {
                sampled.add(full.get(i));
            }
            return sampled;
        }

        return full;
    }
}
