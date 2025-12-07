package hird.repository.specification;

import hird.dto.ForecastRequest;
import hird.model.ModelPrediction;
import org.springframework.data.jpa.domain.Specification;
import jakarta.persistence.criteria.Predicate;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;


public class ModelPredictionSpecification {
    public static Specification<ModelPrediction> matches(ForecastRequest req, int months) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            LocalDate start = LocalDate.now();
            LocalDate end = start.plusMonths(months);

            predicates.add(cb.equal(root.get("city"), req.city()));
            predicates.add(cb.equal(root.get("target"), req.target()));
            predicates.add(cb.equal(root.get("horizonMonths"), months));
            predicates.add(cb.between(root.get("predictDate"), start, end));

            if (req.propertyType() != null)
                predicates.add(cb.equal(root.get("propertyType"), req.propertyType()));

            if (!req.beds().equals("Any"))
                predicates.add(cb.equal(root.get("beds"), Integer.parseInt(req.beds())));

            if (!req.baths().equals("Any"))
                predicates.add(cb.equal(root.get("baths"), Integer.parseInt(req.baths())));

            if (req.sqftMin() != null)
                predicates.add(cb.greaterThanOrEqualTo(root.get("sqftMin"), req.sqftMin()));

            if (req.sqftMax() != null)
                predicates.add(cb.lessThanOrEqualTo(root.get("sqftMax"), req.sqftMax()));

            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }
}

