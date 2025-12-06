package hird.mapper;

import hird.dto.ForecastPointResponse;
import hird.model.ModelPrediction;

public final class ForecastPointMapper {
    public static ForecastPointResponse toResponse(ModelPrediction row) {
        return new ForecastPointResponse(
                row.getPredictDate().toString(),
                row.getYhat(),
                row.getYhatLower(),
                row.getYhatUpper()
        );
    }
}
