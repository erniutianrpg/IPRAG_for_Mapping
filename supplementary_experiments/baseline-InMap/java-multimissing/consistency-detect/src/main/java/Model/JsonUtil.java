package Model;

import Model.Dependency.DependencyData;
import Model.Reflexion.ReflectionModel;
import Model.Target.TargetModel;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.*;
import java.nio.charset.StandardCharsets;

public class JsonUtil {
    public static DependencyData getGSONObject1(File file) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        try {
            String jsonStr = getString(file);
            return gson.fromJson(jsonStr, DependencyData.class);
        } catch (IOException e) {
            System.out.println(e.getMessage());
        }
        return null;
    }

    public static ReflectionModel getGSONObject2(File file) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        try {
            String jsonStr = getString(file);
            return gson.fromJson(jsonStr, ReflectionModel.class);
        } catch (IOException e) {
            System.out.println(e.getMessage());
        }
        return null;
    }


    public static TargetModel getGSONObject3(File file) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonStr;
        try {
            jsonStr = getString(file);
            return gson.fromJson(jsonStr, TargetModel.class);
        } catch (IOException e) {
            System.out.println(e.getMessage());
        }
        return null;
    }
     /*

    public static ConstraintList getGSONObject4(File file) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        try {
            String jsonStr = getString(file);
            return gson.fromJson(jsonStr, ConstraintList.class);
        } catch (IOException e) {
            System.out.println(e.getMessage());
        }
        return null;
    }

    public static Enre getGSONObject5(File file) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        try {
            String jsonStr = getString(file);
            return gson.fromJson(jsonStr, Enre.class);
        } catch (IOException e) {
            System.out.println(e.getMessage());
        }
        return null;
    }

 */

    private static String getString(File file) throws IOException {
        String jsonStr;
        FileReader fileReader = new FileReader(file);
        Reader reader = new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8);
        int ch;
        StringBuilder sb = new StringBuilder();
        while ((ch = reader.read()) != -1) {
            sb.append((char) ch);
        }
        fileReader.close();
        reader.close();
        jsonStr = sb.toString();
        return jsonStr;
    }
/*
    public static void outputDependencyDataToFile(JsonRootBean jsonRootBean, File file) throws IOException {
        System.out.println("Writing a new json...");
        try (Writer writer = new FileWriter(file)) {
            Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
            gson.toJson(jsonRootBean, writer);
        }
        System.out.println("Finished writing");
    }

    public static void outputSmell(ArchitectureSmellOutputDTO architectureSmellOutputDTO, File file) throws IOException {
        System.out.println("Writing a new json...");
        try (Writer writer = new FileWriter(file)) {
            Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
            gson.toJson(architectureSmellOutputDTO, writer);
        }
        System.out.println("Finished writing");
    }

    public static void outputSmellCompare(ArchitectureSmellCompareDTO architectureSmellCompareDTO, File file) throws IOException {
        System.out.println("Writing a new json...");
        try (Writer writer = new FileWriter(file)) {
            Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
            gson.toJson(architectureSmellCompareDTO, writer);
        }
        System.out.println("Finished writing");
    }

    public static void outputInconsist(Inconsist inconsist, File file) throws IOException {
        System.out.println("Writing a new json...");
        try (Writer writer = new FileWriter(file)) {
            Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
            gson.toJson(inconsist, writer);
        }
        System.out.println("Finished writing");
    }

 */
}
