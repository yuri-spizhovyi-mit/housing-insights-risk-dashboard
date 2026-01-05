package maxdev.hird.dto;


import java.util.List;
import java.util.Map;

public record ModelComparisonResponse(
        String city,
        String target,
        List<Integer> horizons,
        Map<String, List<ModelComparisonPoint>> models
) {}
