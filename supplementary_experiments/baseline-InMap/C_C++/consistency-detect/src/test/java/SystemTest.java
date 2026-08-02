//import ReflexionModel.SimilarityScore;
////import ai.onnxruntime.OrtException;
//import entity.ModuleMappingResult;
//import org.apache.lucene.queryparser.classic.ParseException;
//import org.junit.Test;
//
//import java.io.BufferedWriter;
//import java.io.File;
//import java.io.FileWriter;
//import java.io.IOException;
//import java.util.*;
//import java.util.stream.Collectors;
//
//import static org.junit.Assert.assertEquals;
//import org.json.JSONArray;
//import org.json.JSONObject;
//
//public class SystemTest {
//
//    @Test
//    public void testMain() throws IOException, ParseException, InterruptedException {
//        String project="teammates";
//        String projectFolder="E:/Zurich/code/consistency-detect/consistency-detect/"+project;
//        String method = "tfidf";
//        double threshold = 0;
//
//        Map<String, Object> entities = generateEntities(projectFolder, project);
//        Map<String, String> moduleMap = (Map<String, String>) entities.get("moduleMap");
//        List<String> exclusionList = (List<String>) entities.get("exclusionList");
//        Map<String, Set<String>> entityMapping = (Map<String, Set<String>>) entities.get("entityMapping");
//
//
//        ModuleMappingResult result =SimilarityScore.run(moduleMap,projectFolder+"",exclusionList,project,method,threshold);
//        Map<String, String> classToModule = result.getClassToModule();
//        Map<String, List<String>> significantScoresModules = result.getSignificantScoresModules();
//
//        JSONObject json = convertToJSON(classToModule);
//        // OutputJSONto a file
//        try (FileWriter file = new FileWriter(projectFolder+"/classToModuleMapping.json")) {
//            file.write(json.toString(4)); // Use 4 spaces for indentation
//            System.out.println("Successfully Copied JSON Object to File...");
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//
//        JSONObject json2 = convertToJSON2(significantScoresModules);
//        // OutputJSONto a file
//        try (FileWriter file = new FileWriter(projectFolder+"/classTo2ModuleMapping.json")) {
//            file.write(json2.toString(4)); // Use 4 spaces for indentation
//            System.out.println("Successfully Copied JSON Object to File...");
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
////        Map<String, Set<String>> newEntityMapping = transformEntityMapping(entityMapping,classToModule,exclusionList);
//        Map<String, Set<String>> newEntityMapping = replaceExtension(entityMapping);
//        evaluation(newEntityMapping,classToModule);
//    }
//
//    public Map<String, Object> generateEntities(String projectFolder, String project) throws IOException {
//        Map<String, String> moduleMap = new HashMap<>();
////        File file = new File(projectFolder+"/"+project.toLowerCase(Locale.ROOT)+"_accurateModules.txt");
//        File file = new File(projectFolder+"/config_"+project.toLowerCase(Locale.ROOT)+".txt");
//        Scanner scanner = new Scanner(file);
//        boolean isModuleNamesSection = false;
//        boolean isModuleDescriptionsSection = false;
//        boolean isEntityMappingSection = false;
//        boolean isExclusionListSection = false;
//
//        List<String> moduleNames = new ArrayList<>();
//        List<String> moduleDescriptions = new ArrayList<>();
//        Map<String, Set<String>> entityMapping = new HashMap<>();
//        List<String> exclusionList = new ArrayList<>();
//        String currentModule = null;
//        while (scanner.hasNextLine()) {
//            String line = scanner.nextLine().trim();
//
//            if (line.equals("ModuleNames : {")) {
//                isModuleNamesSection = true;
//                continue;
//            }
//            if (line.equals("ModuleDescriptions : {")) {
//                isModuleNamesSection = false;
//                isModuleDescriptionsSection = true;
//                continue;
//            }
//            if (line.equals("EntityMapping : {")) {
//                isModuleDescriptionsSection = false;
//                isEntityMappingSection = true;
//                continue;
//            }
//            if (line.equals("ExclusionList : {")) {
//                isExclusionListSection = true;
//                continue;
//            }
//            if (line.equals("}")) {
//                isModuleNamesSection = false;
//                isModuleDescriptionsSection = false;
//                isEntityMappingSection = false;
//                isExclusionListSection = false;
//                continue;
//            }
//
//            if (isModuleNamesSection) {
//                String moduleName = line.substring(1, line.length() - 1); // remove the quotation marks
//                moduleNames.add(moduleName);
//            }
//
//            if (isModuleDescriptionsSection) {
//                String moduleDescription = line.substring(1, line.length() - 1); // remove the quotation marks
//                moduleDescriptions.add(moduleDescription);
//            }
//
//            if (isEntityMappingSection) {
//                if (line.startsWith("\"MODULE :")) {
//                    currentModule = line.split(":")[1].trim().replaceAll("\"", "");
//                    entityMapping.put(currentModule, new HashSet<>());
//                } else {
//                    if (currentModule != null && !line.isEmpty()) {
//                        line = line.replaceAll("\"", "");
//                        entityMapping.get(currentModule).add(line);
//                    }
//                }
//            }
//            if (isExclusionListSection) {
//                if (!line.isEmpty()){
//                    String excludedClass = line.substring(1, line.length() - 1); // remove the quotation marks
//                    exclusionList.add(excludedClass);
//                }
//            }
//
//        }
//        // Ensure that module names and descriptions lists are of equal size
//        if (moduleNames.size() != moduleDescriptions.size()) {
//            System.out.println("Error: Mismatch in number of module names and descriptions.");
//            return null;
//        }
//
//        // Create map from module names and descriptions
//        for (int i = 0; i < moduleNames.size(); i++) {
//            moduleMap.put(moduleNames.get(i), moduleDescriptions.get(i));
//        }
//
//        scanner.close();
//
//        for (Map.Entry<String, String> entry : moduleMap.entrySet()) {
////            System.out.println("ModuleName: " + entry.getKey() + " ModuleDescription: " + entry.getValue());
//        }
//        // Return a Map containing moduleMap, exclusionList, and entityMapping
//        Map<String, Object> entities = new HashMap<>();
//        entities.put("moduleMap", moduleMap);
//        entities.put("exclusionList", exclusionList);
//        entities.put("entityMapping", entityMapping);
//        return entities;
//    }
//
//    public Map<String, Set<String>> transformEntityMapping(
//            Map<String, Set<String>> entityMapping, Map<String, String> classToModule, List<String> exclusionList) {
//
//        Map<String, Set<String>> newEntityMapping = new HashMap<>();
//
//        for (Map.Entry<String, Set<String>> entry : entityMapping.entrySet()) {
//            Set<String> newValues = new HashSet<>();
//            List<String> packageList = entityMapping.values().stream()
//                    .flatMap(Set::stream)
//                    .collect(Collectors.toList());
////            for (String module : entry.getValue()) {
////                // Retrieve the class names from classToModule that match the module.
////                classToModule.forEach((className, predictedModule) -> {
////                    String actualModule = extractModuleName(className, packageList,exclusionList);
////                    if (module.equals(actualModule)) {
////                        newValues.add(className);
////                    }
////                });
////            }
//            for (String module : entry.getValue()) {
//                if (module.contains("org.apache.tools.ant.taskdefs.AbstractCvsTask")){
//                    int flag=1;
//                }
//
//                for (Map.Entry<String, String> classToModuleEntry : classToModule.entrySet()) {
//                    String className = classToModuleEntry.getKey();
//                    String predictedModule = classToModuleEntry.getValue();
//
//                    // Add print statements to understand the code execution process
////                    System.out.println("Processing class: " + className);
////                    System.out.println("Predicted module: " + predictedModule);
//
//                    String actualModule = extractModuleName(className, packageList, exclusionList);
////                    System.out.println("Actual module: " + actualModule);
//                    if (className.equals("E:\\Architecture\\InconsistencyDetect\\InMap\\test-systems\\Ant\\src\\main\\org\\apache\\tools\\ant\\taskdefs\\AbstractCvsTask.jvtp")){
//                        int flag=1;
//                    }
//
//                    if (module.equals(actualModule)) {
////                        System.out.println("Match found for module: " + module);
//                        newValues.add(className);
//                    }
//                }
//            }
//
//            newEntityMapping.put(entry.getKey(), newValues);
//        }
//
//        return newEntityMapping;
//    }
//    public boolean checkKeysExistence(Map<String, List<String>> newEntityMapping, String className) {
//            boolean exists = false;
//
//            // Check if className exists in any of the values of newEntityMapping
//            for (List<String> classes : newEntityMapping.values()) {
//                if (classes.contains(className)) {
//                    exists = true;
//                    break;
//                }
//            }
//
//            if (exists) {
//                System.out.println(className + " exists in newEntityMapping values.");
//            } else {
//                System.out.println(className + " does NOT exist in newEntityMapping values.");
//            }
//            return exists;
//
//    }
//
//    public void evaluation(Map<String, Set<String>> newEntityMapping, Map<String, String> classToModule) throws IOException {
//        int truePositives = 0;
//        int falsePositives = 0;
//        int falseNegatives = 0;
//        Set<String> falsePositivesSet = new HashSet<>();
//        Set<String> falseNegativesSet = new HashSet<>();
//        // Check each entry in classToModule
//        for (Map.Entry<String, String> entry : classToModule.entrySet()) {
//            String className = entry.getKey();
//            if (className.contains("akka-bbb-fsesl/src/main/java/org/bigbluebutton/freeswitch/voice/freeswitch/actions/CheckIfConfIsRunningCommand.jvtp")){
//                int flag=1;
//            }
////            String originalPath = className;
////            className = originalPath.substring(originalPath.indexOf("src/") ).replace(".jvtp", ".java");
//
//            String predictedModule = entry.getValue();
//
//
//            // CheckclassNamewhether it is in newEntityMappingany module in 
//            String finalClassName = className;
//            boolean classExistsInMapping = newEntityMapping.values().stream()
//                    .anyMatch(module -> module.contains(finalClassName));
//
////Need to consider whether to keep this
//            if (!classExistsInMapping) {
//                continue; // If classNamedoes not exist in newEntityMapping, skip the current iteration
//            }
//
//
//
//
//
//            // If the predicted module correctly contains the class, it is a true positive
//            if (newEntityMapping.get(predictedModule) != null && newEntityMapping.get(predictedModule).contains(className)) {
//                truePositives++;
//            } else {
//                falsePositives++;
//                falsePositivesSet.add(className);
//            }
//        }
//
//
//        // Check for False Negatives
//        for (Map.Entry<String, Set<String>> entry : newEntityMapping.entrySet()) {
//            for (String className : entry.getValue()) {
//                String module=classToModule.get(className);
//                if ((!classToModule.containsKey(className)) || (!classToModule.get(className).equals(entry.getKey()))) {
//                    falseNegatives++;
//                    falseNegativesSet.add(className);
//                }
//            }
//        }
//
//        // Find items that are in falsePositives but not in falseNegatives
//        Set<String> onlyInFalsePositives = new HashSet<>(falsePositivesSet);
//        onlyInFalsePositives.removeAll(falseNegativesSet);
//
//// Find items that are in falseNegatives but not in falsePositives
//        Set<String> onlyInFalseNegatives = new HashSet<>(falseNegativesSet);
//        onlyInFalseNegatives.removeAll(falsePositivesSet);
//
//        int num= 0;
//        for (String key:newEntityMapping.keySet()){
//            for (String value:newEntityMapping.get(key)){
//                if (value.contains("org\\apache\\tools\\ant\\taskdefs\\optional\\jlink\\ConstantPool")){
//                    int flag=1;
//                }
//                num+=1;
//            }
//        }
//
//        double precision = (double) truePositives / (truePositives + falsePositives);
//        double recall = (double) truePositives / (truePositives + falseNegatives);
//
//        System.out.println("Precision: " + precision);
//        System.out.println("Recall: " + recall);
//
//        // Output incorrectly matched content to TXTfile
//        outputFalsePositivesWithCorrections(falsePositivesSet, newEntityMapping, classToModule, "C:\\Users\\XJTU\\Desktop\\false_positives_with_corrections.txt");
//
////        outputErrorsToFile(falseNegativesSet, "false_negatives.txt");
//
//    }
//
//    private void outputFalsePositivesWithCorrections(Set<String> falsePositives, Map<String, Set<String>> newEntityMapping, Map<String, String> classToModule, String filename) throws IOException {
//        BufferedWriter writer = new BufferedWriter(new FileWriter(filename));
//        for (String className : falsePositives) {
//            String predictedModule = classToModule.get(className);
//            String correctModule = findCorrectModule(newEntityMapping, className);
//
//            writer.write("Class: " + className + ", Predicted Module: " + predictedModule + ", Correct Module: " + (correctModule != null ? correctModule : "None"));
//            writer.newLine();
//        }
//        writer.close();
//    }
//
//    // Helper method to find the correct module for a given class
//    private String findCorrectModule(Map<String, Set<String>> newEntityMapping, String className) {
//        for (Map.Entry<String, Set<String>> entry : newEntityMapping.entrySet()) {
//            if (entry.getValue().contains(className)) {
//                return entry.getKey();
//            }
//        }
//        return null; // If the class is not found in the mapping, return null
//    }
//
//    private static String extractModuleName(String className, List<String> packageList, List<String> exclusionList) {
//
//        String test="E:\\Architecture\\InconsistencyDetect\\InMap\\test-systems\\Ant\\src\\main\\org\\apache\\tools\\ant\\util\\java15\\ProxyDiagnostics.java";
//        if (className.equals(test)){
//            int g=1;
//        }
//        String[] parts = className.replaceAll("\\.jvtp","").split("/");  // split by backslash
//
//        // Start from the index where 'src' or 'main' is located
//        int startIndex = -1;
//        for (int i = parts.length - 1; i >= 0; i--) {
//            if (parts[i].equals("src") || parts[i].equals("main") || parts[i].equals("java") || parts[i].equals("sources")) {
//                startIndex = i + 1;
//                break;
//            }
//        }
//        if (startIndex == -1) {
//            return null; // 'src' or 'main' not found
//        }
//
//        for (int endIndex = parts.length - 1; endIndex >= startIndex; endIndex--) {
//            String[] subArray = Arrays.copyOfRange(parts, startIndex, endIndex + 1);
//            String potentialModule = String.join(".", subArray);
//            if (exclusionList.contains(potentialModule)){
//                return null;
//            }
//            if (packageList.contains(potentialModule)) {
//                return potentialModule;
//            }
//        }
//
//        // If no matching module found
//        return null;
//    }
//
//    public static Map<String, Set<String>> replaceExtension(Map<String, Set<String>> originalMap) {
//        Map<String, Set<String>> updatedMap = new HashMap<>();
//
//        for (Map.Entry<String, Set<String>> entry : originalMap.entrySet()) {
//            Set<String> updatedList = new HashSet<>();
//            for (String filename : entry.getValue()) {
//                String updatedFilename = filename.replace(".java", ".jvtp");
//                updatedList.add(updatedFilename);
//            }
//            updatedMap.put(entry.getKey(), updatedList);
//        }
//
//        return updatedMap;
//    }
//
//    public static JSONObject convertToJSON(Map<String, String> classToModule) {
//        JSONObject root = new JSONObject();
//        root.put("@schemaVersion", "1/0");
//        root.put("name", "clustering");
//
//        // Use Mapto organize different modules and their corresponding classes
//        Map<String, List<String>> modules = new HashMap<>();
//        for (Map.Entry<String, String> entry : classToModule.entrySet()) {
//            String className = entry.getKey().replace(".jvtp", ".java");
//            modules.computeIfAbsent(entry.getValue(), k -> new ArrayList<>()).add(className);
//        }
//
//        JSONArray structure = new JSONArray();
//        for (Map.Entry<String, List<String>> module : modules.entrySet()) {
//            JSONObject group = new JSONObject();
//            group.put("@type", "group");
//            group.put("name", module.getKey());
//
//            JSONArray nested = new JSONArray();
//            for (String className : module.getValue()) {
//                JSONObject item = new JSONObject();
//                item.put("@type", "item");
//                item.put("name", className);
//                nested.put(item);
//            }
//
//            group.put("nested", nested);
//            structure.put(group);
//        }
//
//        root.put("structure", structure);
//
//        return root;
//    }
//
//    public static JSONObject convertToJSON2(Map<String, List<String>> significantScoresModules) {
//        JSONObject root = new JSONObject();
//
//        for (Map.Entry<String, List<String>> entry : significantScoresModules.entrySet()) {
//            String className = entry.getKey().replace(".jvtp", ".java");
//            List<String> modules = entry.getValue();
//
//            // Add the class name and corresponding module list to JSON
//            root.put(className, modules);
//        }
//
//        return root;}
//}
