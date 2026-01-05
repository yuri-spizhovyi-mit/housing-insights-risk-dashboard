package maxdev.hird.service;

import maxdev.hird.domain.exceptions.ResourceNotFoundException;
import maxdev.hird.repository.ModelPredictionRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CitiesService {
    private final ModelPredictionRepository modelPredictionRepository;

    public CitiesService(ModelPredictionRepository modelPredictionRepository){
        this.modelPredictionRepository = modelPredictionRepository;
    }

    @Cacheable(value = "CITIES_CACHE")
    public List<String> retrieveCities(){
        List<String> cities = modelPredictionRepository.findDistinctCities();

        if(cities.isEmpty()){
            throw new ResourceNotFoundException("No cities found.");
        }

        return cities;
    }
}
