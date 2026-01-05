package maxdev.hird.model;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Objects;

@Getter
@Setter
@NoArgsConstructor
@Embeddable
public class ModelComparisonId {
    private String city;
    private String target;

    @Column(name = "horizon_months")
    private Integer horizonMonths;

    @Column(name = "model_name")
    private String modelName;


    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ModelComparisonId that)) {
            return false;
        }

        return Objects.equals(city, that.city)
                && Objects.equals(target, that.target)
                && Objects.equals(horizonMonths, that.horizonMonths)
                && Objects.equals(modelName, that.modelName);
    }

    @Override
    public int hashCode() {
        return Objects.hash(city, target, horizonMonths, modelName);
    }
}