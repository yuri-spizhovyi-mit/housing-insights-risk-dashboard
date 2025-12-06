package hird.util;

public class HousingMarketClassifier {

    private HousingMarketClassifier() {}


    public static String mapAffordability(double v) {
        if (v >= 0.8) return "Tight";
        if (v >= 0.5) return "Moderate";
        return "Comfortable";
    }

    public static String mapPriceToRent(double v) {
        if (v >= 0.7) return "Elevated";
        if (v >= 0.4) return "Balanced";
        return "Attractive";
    }

    public static String mapInventory(double v) {
        if (v < 0.4) return "Low";
        if (v < 0.7) return "Adequate";
        return "High";
    }
}
