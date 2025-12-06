package hird.service;

import hird.dto.ForecastPointResponse;
import hird.dto.ForecastRequest;
import hird.dto.ForecastResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.model.ModelPrediction;
import hird.repository.ModelPredictionRepository;
import hird.repository.specification.ModelPredictionSpecification;
import hird.service.collector.ForecastPointCollector;
import hird.util.HorizonParser;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ForecastService {
    private final ModelPredictionRepository repository;

    public ForecastService(ModelPredictionRepository repository){
        this.repository = repository;
    }

    public ForecastResponse retrieveForecast(ForecastRequest req){
        int months = HorizonParser.toMonths(req.horizon());

        Specification<ModelPrediction> specification = ModelPredictionSpecification.matches(req, months);
        List<ModelPrediction> rows = repository.findAll(specification);

        if(rows.isEmpty())
            throw new ResourceNotFoundException("No forecast data for " + req.city());

        List<ForecastPointResponse> points = ForecastPointCollector.collect(rows);
        return new ForecastResponse(req.city(), req.target(), months, points);
    }
}
