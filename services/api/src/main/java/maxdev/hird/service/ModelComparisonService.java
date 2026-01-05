package maxdev.hird.service;

import maxdev.hird.domain.exceptions.ResourceNotFoundException;
import maxdev.hird.dto.ModelComparisonPoint;
import maxdev.hird.dto.ModelComparisonResponse;
import maxdev.hird.model.ModelComparison;
import maxdev.hird.repository.ModelComparisonRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class ModelComparisonService {

    private final ModelComparisonRepository modelComparisonRepository;

    public ModelComparisonService(ModelComparisonRepository modelComparisonRepository) {
        this.modelComparisonRepository = modelComparisonRepository;
    }

    @Cacheable(
            value = "MODEL-COMPARISON_CACHE",
            key = "#city.toLowerCase() + ':' + #target.toLowerCase()"
    )
    public ModelComparisonResponse retrieveComparisonData(String city, String target) {
        List<ModelComparison> rows = modelComparisonRepository.findForComparison(city, target);

        if (rows.isEmpty()) {
            throw new ResourceNotFoundException("No comparison data for " + city + ", and " + target);
        }

        return toResponse(city, target, rows);
    }

    private ModelComparisonResponse toResponse(String city, String target, List<ModelComparison> rows) {
        Set<Integer> horizons = new LinkedHashSet<>();
        Map<String, List<ModelComparisonPoint>> models = new LinkedHashMap<>();

        rows.forEach(row -> {
            int h = row.getId().getHorizonMonths();
            String m = cleanModelName(row.getId().getModelName());

            horizons.add(h);
            models.computeIfAbsent(m, k -> new ArrayList<>())
                    .add(new ModelComparisonPoint(h, row.getMae(), row.getMape(), row.getRmse(), row.getMse(), row.getR2()));
        });

        return new ModelComparisonResponse(city, target, new ArrayList<>(horizons), models);
    }

    private String cleanModelName(String modelName) {
        return modelName == null ? "" : modelName.replace("_backtest", "");
    }
}
