package hird.service;

import hird.dto.RiskGaugeIndicator;
import hird.dto.RiskGaugeResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.model.RiskGauge;
import hird.repository.RiskGaugeRepository;
import hird.service.collector.RiskGaugeIndexCollector;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static hird.util.HousingMarketClassifier.*;

@Service
public class RiskGaugeService {
    private final RiskGaugeRepository repository;

    public RiskGaugeService(RiskGaugeRepository repository){
        this.repository = repository;
    }

    public RiskGaugeResponse retrieveRiskGaugeData(String city){
        List<RiskGauge> rows = repository.findByCityOrderByPredictDateDesc(city);

        if(rows.isEmpty())
            throw new ResourceNotFoundException("No risk data for " + city);

        Map<String, Double> index = RiskGaugeIndexCollector.collect(rows);

        String date = rows.get(0).getPredictDate().toString();
        Integer score = (int) Math.round(index.getOrDefault("composite_index", 0.0) * 100);

        List<RiskGaugeIndicator> indicators = List.of(
                new RiskGaugeIndicator("Affordability", mapAffordability(index.getOrDefault("affordability", 0.0))),
                new RiskGaugeIndicator("Price-to-Rent", mapPriceToRent(index.getOrDefault("price_to_rent", 0.0))),
                new RiskGaugeIndicator("Inventory", mapInventory(index.getOrDefault("inventory", 0.0)))
        );

        return new RiskGaugeResponse(city, date, score, indicators);
    }
}
