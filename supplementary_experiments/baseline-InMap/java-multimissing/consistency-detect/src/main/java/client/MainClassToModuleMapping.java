package client;
import ReflexionModel.SimilarityScore;
//import ai.onnxruntime.OrtException;
import entity.ModuleMappingResult;
import org.apache.lucene.queryparser.classic.ParseException;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;
import java.io.*;

public class MainClassToModuleMapping {

    public static void main(String[] args) throws IOException, ParseException, InterruptedException {
        if (args.length < 3) {
            System.out.println("Usage: java MainClassToModuleMapping <project name> <projectFolder dir> <The file name that contains the module information>");
            return;
        }

        String project = args[0];
        String projectFolder = args[1]+'/'+project;
        String notaccurateModulesFile = args[2];
        String method = args[3];
        double threshold = Double.parseDouble(args[4]);
        String outputFolder = args[5];

        Map<String, Object> entities = generateEntities(projectFolder, project, notaccurateModulesFile);
        Map<String, String> moduleMap = (Map<String, String>) entities.get("moduleMap");
        List<String> exclusionList = (List<String>) entities.get("exclusionList");
        Map<String, Set<String>> entityMapping = (Map<String, Set<String>>) entities.get("entityMapping");


        ModuleMappingResult result = SimilarityScore.run(moduleMap,projectFolder+"",exclusionList,project,method,threshold);
        Map<String, String> classToModule = result.getClassToModule();
        Map<String, String> classToModule1 = result.getClassToModule1();
        Map<String, Map<String, Double>> classToModuleScores = result.getclassToModuleScores();


        // OutputJSONto a file
        if (classToModule != null) {
            JSONObject json = convertToJSON(classToModule);
            try (FileWriter file = new FileWriter(outputFolder+"/file-module_mapping-tfidf.json")) {
                file.write(json.toString(4)); // Use 4 spaces for indentation
                System.out.println("Successfully Generated File-Module Mapping for recovering...");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (classToModule1 != null) {
            JSONObject json1 = convertToJSON(classToModule1);
            // OutputJSONto a file
            try (FileWriter file = new FileWriter(outputFolder + "/few-shot_mapping.json")) {
                file.write(json1.toString(4)); // Use 4 spaces for indentation
                System.out.println("Successfully Generated File-Module Mapping for mapping...");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (classToModuleScores != null) {
            exportClassToModuleScoresToCSV(classToModuleScores, outputFolder + "/tfidf-file-module_scores.csv");
        }
    }

    public static Map<String, Object> generateEntities(String projectFolder, String project, String notaccurateModulesFile) throws IOException {
        Map<String, String> moduleMap = new HashMap<>();
        File file = new File(notaccurateModulesFile);
        Scanner scanner = new Scanner(file);
        boolean isModuleNamesSection = false;
        boolean isModuleDescriptionsSection = false;
        boolean isEntityMappingSection = false;
        boolean isExclusionListSection = false;

        List<String> moduleNames = new ArrayList<>();
        List<String> moduleDescriptions = new ArrayList<>();
        Map<String, Set<String>> entityMapping = new HashMap<>();
        List<String> exclusionList = new ArrayList<>();
        String currentModule = null;
        while (scanner.hasNextLine()) {
            String line = scanner.nextLine().trim();

            if (line.equals("ModuleNames : {")) {
                isModuleNamesSection = true;
                continue;
            }
            if (line.equals("ModuleDescriptions : {")) {
                isModuleNamesSection = false;
                isModuleDescriptionsSection = true;
                continue;
            }
            if (line.equals("EntityMapping : {")) {
                isModuleDescriptionsSection = false;
                isEntityMappingSection = true;
                continue;
            }
            if (line.equals("ExclusionList : {")) {
                isExclusionListSection = true;
                continue;
            }
            if (line.equals("}")) {
                isModuleNamesSection = false;
                isModuleDescriptionsSection = false;
                isEntityMappingSection = false;
                isExclusionListSection = false;
                continue;
            }

            if (isModuleNamesSection) {
                String moduleName = line.substring(1, line.length() - 1); // remove the quotation marks
                moduleNames.add(moduleName);
            }

            if (isModuleDescriptionsSection) {
                String moduleDescription = line.substring(1, line.length() - 1); // remove the quotation marks
                moduleDescriptions.add(moduleDescription);
            }

            if (isEntityMappingSection) {
                if (line.startsWith("\"MODULE :")) {
                    currentModule = line.split(":")[1].trim().replaceAll("\"", "");
                    entityMapping.put(currentModule, new HashSet<>());
                } else {
                    if (currentModule != null && !line.isEmpty()) {
                        line = line.replaceAll("\"", "");
                        entityMapping.get(currentModule).add(line);
                    }
                }
            }
            if (isExclusionListSection) {
                if (!line.isEmpty()){
                    String excludedClass = line.substring(1, line.length() - 1); // remove the quotation marks
                    exclusionList.add(excludedClass);
                }
            }

        }
        // Ensure that module names and descriptions lists are of equal size
        if (moduleNames.size() != moduleDescriptions.size()) {
            System.out.println("Error: Mismatch in number of module names and descriptions.");
            return null;
        }

        // Create map from module names and descriptions
        for (int i = 0; i < moduleNames.size(); i++) {
            moduleMap.put(moduleNames.get(i), moduleDescriptions.get(i));
        }

        scanner.close();

        for (Map.Entry<String, String> entry : moduleMap.entrySet()) {
//            System.out.println("ModuleName: " + entry.getKey() + " ModuleDescription: " + entry.getValue());
        }
        // Return a Map containing moduleMap, exclusionList, and entityMapping
        Map<String, Object> entities = new HashMap<>();
        entities.put("moduleMap", moduleMap);
        entities.put("exclusionList", exclusionList);
        entities.put("entityMapping", entityMapping);
        return entities;
    }
    public static JSONObject convertToJSON(Map<String, String> classToModule) {
        JSONObject root = new JSONObject();
        root.put("@schemaVersion", "1/0");
        root.put("name", "clustering");

        // Use Mapto organize different modules and their corresponding classes
        Map<String, List<String>> modules = new HashMap<>();
        for (Map.Entry<String, String> entry : classToModule.entrySet()) {
            String className = entry.getKey().replace(".jvtp", ".java");
            modules.computeIfAbsent(entry.getValue(), k -> new ArrayList<>()).add(className);
        }

        JSONArray structure = new JSONArray();
        for (Map.Entry<String, List<String>> module : modules.entrySet()) {
            JSONObject group = new JSONObject();
            group.put("@type", "group");
            group.put("name", module.getKey());

            JSONArray nested = new JSONArray();
            for (String className : module.getValue()) {
                JSONObject item = new JSONObject();
                item.put("@type", "item");
                item.put("name", className);
                nested.put(item);
            }

            group.put("nested", nested);
            structure.put(group);
        }

        root.put("structure", structure);

        return root;
    }

    public static void exportClassToModuleScoresToCSV(Map<String, Map<String, Double>> classToModuleScores, String outputPath) {
        if (classToModuleScores == null || classToModuleScores.isEmpty()) {
            System.out.println("classToModuleScores is empty or null. Skipping CSV export.");
            return;
        }

        // Collect all module names (column names)
        Set<String> allModules = new TreeSet<>();
        for (Map<String, Double> moduleScores : classToModuleScores.values()) {
            allModules.addAll(moduleScores.keySet());
        }

        // Write CSV file
        try (PrintWriter writer = new PrintWriter(new FileWriter(outputPath))) {
            // Write header
            writer.print("file_path");
            for (String module : allModules) {
                writer.print("," + module);
            }
            writer.println(",best_module,best_likelihood");

            // Write each row
            for (Map.Entry<String, Map<String, Double>> entry : classToModuleScores.entrySet()) {
                String filePath = entry.getKey().replace(".jvtp", ".java");;
                Map<String, Double> moduleScores = entry.getValue();

                // find  best_module and best_likelihood
                String bestModule = "";
                double bestScore = Double.NEGATIVE_INFINITY;
                for (Map.Entry<String, Double> scoreEntry : moduleScores.entrySet()) {
                    if (scoreEntry.getValue() > bestScore) {
                        bestScore = scoreEntry.getValue();
                        bestModule = scoreEntry.getKey();
                    }
                }

                // Write row data
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
}
