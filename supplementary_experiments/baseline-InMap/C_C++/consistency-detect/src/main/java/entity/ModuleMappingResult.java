package entity;

import java.util.List;
import java.util.Map;

public class ModuleMappingResult {
    private Map<String, String> classToModule;
    private Map<String, String> classToModule1;
    private Map<String, List<String>> significantScoresModules;
    private Map<String, Map<String, Double>> classToModuleScores;

    public static ModuleMappingResult forScores(Map<String, Map<String, Double>> classToModuleScores) {
        return new ModuleMappingResult(null, null, null, classToModuleScores);
    }

    public ModuleMappingResult(Map<String, String> classToModule, Map<String, String> classToModule1, Map<String, List<String>> significantScoresModules, Map<String, Map<String, Double>> classToModuleScores) {
        this.classToModule = classToModule;
        this.classToModule1 = classToModule1;
        this.significantScoresModules = significantScoresModules;
        this.classToModuleScores = classToModuleScores;
    }

    public Map<String, String> getClassToModule() {
        return classToModule;
    }

    public Map<String, String> getClassToModule1() {
        return classToModule1;
    }

    public Map<String, List<String>> getSignificantScoresModules() {
        return significantScoresModules;
    }

    public Map<String, Map<String, Double>> getclassToModuleScores() {
        return classToModuleScores;
    }
}
