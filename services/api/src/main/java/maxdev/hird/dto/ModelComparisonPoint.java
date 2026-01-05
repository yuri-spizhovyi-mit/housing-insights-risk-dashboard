package maxdev.hird.dto;

public record ModelComparisonPoint(
        int horizon,
        Double mae,
        Double mape,
        Double rmse,
        Double mse,
        Double r2
) {}
