package hird.service.collector;

import hird.dto.ForecastPointResponse;
import hird.mapper.ForecastPointMapper;
import hird.model.ModelPrediction;

import java.time.LocalDate;
import java.util.*;

public final class ForecastPointCollector {

    private ForecastPointCollector() {}

    public static List<ForecastPointResponse> collect(List<ModelPrediction> rows) {
        TreeMap<LocalDate, ForecastPointResponse> map = new TreeMap<>();

        for (ModelPrediction row : rows) {
            map.putIfAbsent(
                    row.getPredictDate(),
                    ForecastPointMapper.toResponse(row)
            );
        }

        return new ArrayList<>(map.values());
    }
}
