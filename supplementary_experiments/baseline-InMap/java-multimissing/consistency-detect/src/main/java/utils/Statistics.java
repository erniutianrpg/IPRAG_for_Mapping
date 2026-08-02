package utils;
import java.util.*;

public class Statistics {
    public static double mean(List<Double> data) {
        double sum = 0.0;
        for (double a : data)
            sum += a;
        return sum / data.size();
    }

    public static double stddev(List<Double> data, double mean) {
        double sum = 0.0;
        for (double a : data)
            sum += (a - mean) * (a - mean);
        return Math.sqrt(sum / data.size());
    }
}
