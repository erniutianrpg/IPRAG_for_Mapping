package client;

import ReflexionModel.SimilarityScore;
import entity.ModuleMappingResult;
import org.apache.lucene.queryparser.classic.ParseException;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;
import java.util.TreeSet;

public class MainClassToModuleMapping {

    public static void main(String[] args) throws IOException, ParseException {
        if (args.length < 6) {
            System.out.println("Usage: java MainClassToModuleMapping <project name> <projectFolder dir> <module information file> tfidf <threshold> <outputFolder> [java|python|cpp]");
            return;
        }

        String project = args[0];
        String projectFolder = args[1] + '/' + project;
        String moduleInfoFile = args[2];
        String method = args[3];
        double threshold = Double.parseDouble(args[4]);
        String outputFolder = args[5];
        String language = args.length >= 7 ? normalizeLanguage(args[6]) : "cpp";
        String processedSuffix = getProcessedSuffix(language);
        String sourceSuffix = getSourceSuffix(language);

        if (!"tfidf".equalsIgnoreCase(method)) {
            throw new IllegalArgumentException("Only tfidf is supported. Received method: " + method);
        }

        Map<String, Object> entities = generateEntities(moduleInfoFile);
        if (entities == null) {
            return;
        }
        Map<String, String> moduleMap = (Map<String, String>) entities.get("moduleMap");
        List<String> exclusionList = (List<String>) entities.get("exclusionList");

        ModuleMappingResult result = SimilarityScore.run(moduleMap, projectFolder, exclusionList, project, "tfidf", threshold, language);
        Map<String, Map<String, Double>> classToModuleScores = result.getclassToModuleScores();
        exportClassToModuleScoresToCSV(classToModuleScores, outputFolder + "/tfidf-file-module_scores.csv", processedSuffix, sourceSuffix);
    }

    public static Map<String, Object> generateEntities(String moduleInfoFile) throws IOException {
        Map<String, String> moduleMap = new HashMap<>();
        File file = new File(moduleInfoFile);
        Scanner scanner = new Scanner(file, StandardCharsets.UTF_8.name());
        boolean isModuleNamesSection = false;
        boolean isModuleDescriptionsSection = false;
        boolean isExclusionListSection = false;

        List<String> moduleNames = new ArrayList<>();
        List<String> moduleDescriptions = new ArrayList<>();
        List<String> exclusionList = new ArrayList<>();
        while (scanner.hasNextLine()) {
            String line = scanner.nextLine().replace("\uFEFF", "").trim();

            if (line.equals("ModuleNames : {")) {
                isModuleNamesSection = true;
                continue;
            }
            if (line.equals("ModuleDescriptions : {")) {
                isModuleNamesSection = false;
                isModuleDescriptionsSection = true;
                continue;
            }
            if (line.equals("ExclusionList : {")) {
                isModuleDescriptionsSection = false;
                isExclusionListSection = true;
                continue;
            }
            if (line.equals("}")) {
                isModuleNamesSection = false;
                isModuleDescriptionsSection = false;
                isExclusionListSection = false;
                continue;
            }

            if (isModuleNamesSection) {
                moduleNames.add(unquote(line));
            }

            if (isModuleDescriptionsSection) {
                moduleDescriptions.add(unquote(line));
            }

            if (isExclusionListSection && !line.isEmpty()) {
                exclusionList.add(unquote(line));
            }
        }
        scanner.close();

        if (moduleNames.size() != moduleDescriptions.size()) {
            System.out.println("Error: Mismatch in number of module names and descriptions.");
            return null;
        }

        for (int i = 0; i < moduleNames.size(); i++) {
            moduleMap.put(moduleNames.get(i), moduleDescriptions.get(i));
        }

        Map<String, Object> entities = new HashMap<>();
        entities.put("moduleMap", moduleMap);
        entities.put("exclusionList", exclusionList);
        return entities;
    }

    public static void exportClassToModuleScoresToCSV(Map<String, Map<String, Double>> classToModuleScores, String outputPath, String processedSuffix, String sourceSuffix) {
        if (classToModuleScores == null || classToModuleScores.isEmpty()) {
            System.out.println("classToModuleScores is empty or null. Skipping CSV export.");
            return;
        }

        Set<String> allModules = new TreeSet<>();
        for (Map<String, Double> moduleScores : classToModuleScores.values()) {
            allModules.addAll(moduleScores.keySet());
        }

        try (PrintWriter writer = new PrintWriter(new FileWriter(outputPath))) {
            writer.print("file_path");
            for (String module : allModules) {
                writer.print("," + module);
            }
            writer.println(",best_module,best_likelihood");

            for (Map.Entry<String, Map<String, Double>> entry : classToModuleScores.entrySet()) {
                String filePath = restoreSourcePath(entry.getKey(), processedSuffix, sourceSuffix);
                Map<String, Double> moduleScores = entry.getValue();

                String bestModule = "";
                double bestScore = Double.NEGATIVE_INFINITY;
                for (Map.Entry<String, Double> scoreEntry : moduleScores.entrySet()) {
                    if (scoreEntry.getValue() > bestScore) {
                        bestScore = scoreEntry.getValue();
                        bestModule = scoreEntry.getKey();
                    }
                }

                writer.print(filePath);
                for (String module : allModules) {
                    double score = moduleScores.getOrDefault(module, 0.0);
                    writer.print("," + score);
                }
                writer.println("," + bestModule + "," + bestScore);
            }

            System.out.println("Successfully exported class-to-module scores to CSV: " + outputPath);
        } catch (IOException e) {
            System.err.println("Error writing CSV file: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static String unquote(String value) {
        return value.trim().replaceAll("^\"|\"$", "");
    }

    private static String normalizeLanguage(String language) {
        if (language == null) {
            return "cpp";
        }
        String normalized = language.trim().toLowerCase();
        if (normalized.equals("py") || normalized.equals("python")) {
            return "python";
        }
        if (normalized.equals("c") || normalized.equals("cc") || normalized.equals("cpp")
                || normalized.equals("cxx") || normalized.equals("c++")) {
            return "cpp";
        }
        return "java";
    }

    private static String getProcessedSuffix(String language) {
        String normalized = normalizeLanguage(language);
        if (normalized.equals("python")) {
            return ".pytp";
        }
        if (normalized.equals("cpp")) {
            return ".cttp";
        }
        return ".jvtp";
    }

    private static String getSourceSuffix(String language) {
        String normalized = normalizeLanguage(language);
        if (normalized.equals("python")) {
            return ".py";
        }
        if (normalized.equals("cpp")) {
            return "";
        }
        return ".java";
    }

    private static String restoreSourcePath(String path, String processedSuffix, String sourceSuffix) {
        if (path.endsWith(processedSuffix)) {
            return path.substring(0, path.length() - processedSuffix.length()) + sourceSuffix;
        }
        return path;
    }
}
