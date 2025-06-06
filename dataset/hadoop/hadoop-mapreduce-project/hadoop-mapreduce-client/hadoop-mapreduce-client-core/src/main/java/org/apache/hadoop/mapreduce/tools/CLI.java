/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.hadoop.mapreduce.tools;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.hadoop.classification.InterfaceAudience;
import org.apache.hadoop.classification.InterfaceStability;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.ipc.RemoteException;
import org.apache.hadoop.mapred.JobConf;
import org.apache.hadoop.mapred.TIPStatus;
import org.apache.hadoop.mapreduce.Cluster;
import org.apache.hadoop.mapreduce.Counters;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.JobID;
import org.apache.hadoop.mapreduce.JobPriority;
import org.apache.hadoop.mapreduce.JobStatus;
import org.apache.hadoop.mapreduce.TaskAttemptID;
import org.apache.hadoop.mapreduce.TaskCompletionEvent;
import org.apache.hadoop.mapreduce.TaskReport;
import org.apache.hadoop.mapreduce.TaskTrackerInfo;
import org.apache.hadoop.mapreduce.TaskType;
import org.apache.hadoop.mapreduce.jobhistory.HistoryViewer;
import org.apache.hadoop.mapreduce.v2.LogParams;
import org.apache.hadoop.security.AccessControlException;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;
import org.apache.hadoop.yarn.server.nodemanager.containermanager.logaggregation.LogDumper;

/**
 * Interprets the map reduce cli options 
 */
@InterfaceAudience.Public
@InterfaceStability.Stable
public class CLI extends Configured implements Tool {
  private static final Log LOG = LogFactory.getLog(CLI.class);
  private Cluster cluster;

  public CLI() {
  }
  
  public CLI(Configuration conf) {
    setConf(conf);
  }
  
  public int run(String[] argv) throws Exception {
    int exitCode = -1;
    if (argv.length < 1) {
      displayUsage("");
      return exitCode;
    }    
    // process arguments
    String cmd = argv[0];
    String submitJobFile = null;
    String jobid = null;
    String taskid = null;
    String historyFile = null;
    String counterGroupName = null;
    String counterName = null;
    JobPriority jp = null;
    String taskType = null;
    String taskState = null;
    int fromEvent = 0;
    int nEvents = 0;
    boolean getStatus = false;
    boolean getCounter = false;
    boolean killJob = false;
    boolean listEvents = false;
    boolean viewHistory = false;
    boolean viewAllHistory = false;
    boolean listJobs = false;
    boolean listAllJobs = false;
    boolean listActiveTrackers = false;
    boolean listBlacklistedTrackers = false;
    boolean displayTasks = false;
    boolean killTask = false;
    boolean failTask = false;
    boolean setJobPriority = false;
    boolean logs = false;

    if ("-submit".equals(cmd)) {
      if (argv.length != 2) {
        displayUsage(cmd);
        return exitCode;
      }
      submitJobFile = argv[1];
    } else if ("-status".equals(cmd)) {
      if (argv.length != 2) {
        displayUsage(cmd);
        return exitCode;
      }
      jobid = argv[1];
      getStatus = true;
    } else if("-counter".equals(cmd)) {
      if (argv.length != 4) {
        displayUsage(cmd);
        return exitCode;
      }
      getCounter = true;
      jobid = argv[1];
      counterGroupName = argv[2];
      counterName = argv[3];
    } else if ("-kill".equals(cmd)) {
      if (argv.length != 2) {
        displayUsage(cmd);
        return exitCode;
      }
      jobid = argv[1];
      killJob = true;
    } else if ("-set-priority".equals(cmd)) {
      if (argv.length != 3) {
        displayUsage(cmd);
        return exitCode;
      }
      jobid = argv[1];
      try {
        jp = JobPriority.valueOf(argv[2]); 
      } catch (IllegalArgumentException iae) {
        LOG.info(iae);
        displayUsage(cmd);
        return exitCode;
      }
      setJobPriority = true; 
    } else if ("-events".equals(cmd)) {
      if (argv.length != 4) {
        displayUsage(cmd);
        return exitCode;
      }
      jobid = argv[1];
      fromEvent = Integer.parseInt(argv[2]);
      nEvents = Integer.parseInt(argv[3]);
      listEvents = true;
    } else if ("-history".equals(cmd)) {
      if (argv.length != 2 && !(argv.length == 3 && "all".equals(argv[1]))) {
         displayUsage(cmd);
         return exitCode;
      }
      viewHistory = true;
      if (argv.length == 3 && "all".equals(argv[1])) {
        viewAllHistory = true;
        historyFile = argv[2];
      } else {
        historyFile = argv[1];
      }
    } else if ("-list".equals(cmd)) {
      if (argv.length != 1 && !(argv.length == 2 && "all".equals(argv[1]))) {
        displayUsage(cmd);
        return exitCode;
      }
      if (argv.length == 2 && "all".equals(argv[1])) {
        listAllJobs = true;
      } else {
        listJobs = true;
      }
    } else if("-kill-task".equals(cmd)) {
      if (argv.length != 2) {
        displayUsage(cmd);
        return exitCode;
      }
      killTask = true;
      taskid = argv[1];
    } else if("-fail-task".equals(cmd)) {
      if (argv.length != 2) {
        displayUsage(cmd);
        return exitCode;
      }
      failTask = true;
      taskid = argv[1];
    } else if ("-list-active-trackers".equals(cmd)) {
      if (argv.length != 1) {
        displayUsage(cmd);
        return exitCode;
      }
      listActiveTrackers = true;
    } else if ("-list-blacklisted-trackers".equals(cmd)) {
      if (argv.length != 1) {
        displayUsage(cmd);
        return exitCode;
      }
      listBlacklistedTrackers = true;
    } else if ("-list-attempt-ids".equals(cmd)) {
      if (argv.length != 4) {
        displayUsage(cmd);
        return exitCode;
      }
      jobid = argv[1];
      taskType = argv[2];
      taskState = argv[3];
      displayTasks = true;
    } else if ("-logs".equals(cmd)) {
      if (argv.length == 2 || argv.length ==3) {
        logs = true;
        jobid = argv[1];
        if (argv.length == 3) {
          taskid = argv[2];
        }  else {
          taskid = null;
        }
      } else {
        displayUsage(cmd);
        return exitCode;
      }
    } else {
      displayUsage(cmd);
      return exitCode;
    }

    // initialize cluster
    cluster = new Cluster(getConf());
        
    // Submit the request
    try {
      if (submitJobFile != null) {
        Job job = Job.getInstance(new JobConf(submitJobFile));
        job.submit();
        System.out.println("Created job " + job.getJobID());
        exitCode = 0;
      } else if (getStatus) {
        Job job = cluster.getJob(JobID.forName(jobid));
        if (job == null) {
          System.out.println("Could not find job " + jobid);
        } else {
          Counters counters = job.getCounters();
          System.out.println();
          System.out.println(job);
          if (counters != null) {
            System.out.println(counters);
          } else {
            System.out.println("Counters not available. Job is retired.");
          }
          exitCode = 0;
        }
      } else if (getCounter) {
        Job job = cluster.getJob(JobID.forName(jobid));
        if (job == null) {
          System.out.println("Could not find job " + jobid);
        } else {
          Counters counters = job.getCounters();
          if (counters == null) {
            System.out.println("Counters not available for retired job " + 
            jobid);
            exitCode = -1;
          } else {
            System.out.println(getCounter(counters,
              counterGroupName, counterName));
            exitCode = 0;
          }
        }
      } else if (killJob) {
        Job job = cluster.getJob(JobID.forName(jobid));
        if (job == null) {
          System.out.println("Could not find job " + jobid);
        } else {
          job.killJob();
          System.out.println("Killed job " + jobid);
          exitCode = 0;
        }
      } else if (setJobPriority) {
        Job job = cluster.getJob(JobID.forName(jobid));
        if (job == null) {
          System.out.println("Could not find job " + jobid);
        } else {
          job.setPriority(jp);
          System.out.println("Changed job priority.");
          exitCode = 0;
        } 
      } else if (viewHistory) {
        viewHistory(historyFile, viewAllHistory);
        exitCode = 0;
      } else if (listEvents) {
        listEvents(cluster.getJob(JobID.forName(jobid)), fromEvent, nEvents);
        exitCode = 0;
      } else if (listJobs) {
        listJobs(cluster);
        exitCode = 0;
      } else if (listAllJobs) {
        listAllJobs(cluster);
        exitCode = 0;
      } else if (listActiveTrackers) {
        listActiveTrackers(cluster);
        exitCode = 0;
      } else if (listBlacklistedTrackers) {
        listBlacklistedTrackers(cluster);
        exitCode = 0;
      } else if (displayTasks) {
        displayTasks(cluster.getJob(JobID.forName(jobid)), taskType, taskState);
      } else if(killTask) {
        TaskAttemptID taskID = TaskAttemptID.forName(taskid);
        Job job = cluster.getJob(taskID.getJobID());
        if (job == null) {
          System.out.println("Could not find job " + jobid);
        } else if (job.killTask(taskID)) {
          System.out.println("Killed task " + taskid);
          exitCode = 0;
        } else {
          System.out.println("Could not kill task " + taskid);
          exitCode = -1;
        }
      } else if(failTask) {
        TaskAttemptID taskID = TaskAttemptID.forName(taskid);
        Job job = cluster.getJob(taskID.getJobID());
        if (job == null) {
            System.out.println("Could not find job " + jobid);
        } else if(job.failTask(taskID)) {
          System.out.println("Killed task " + taskID + " by failing it");
          exitCode = 0;
        } else {
          System.out.println("Could not fail task " + taskid);
          exitCode = -1;
        }
      } else if (logs) {
        try {
        JobID jobID = JobID.forName(jobid);
        TaskAttemptID taskAttemptID = TaskAttemptID.forName(taskid);
        LogParams logParams = cluster.getLogParams(jobID, taskAttemptID);
        LogDumper logDumper = new LogDumper();
        logDumper.setConf(getConf());
        logDumper.dumpAContainersLogs(logParams.getApplicationId(),
            logParams.getContainerId(), logParams.getNodeId(),
            logParams.getOwner());
        } catch (IOException e) {
          if (e instanceof RemoteException) {
            throw e;
          } 
          System.out.println(e.getMessage());
        }
      }
    } catch (RemoteException re) {
      IOException unwrappedException = re.unwrapRemoteException();
      if (unwrappedException instanceof AccessControlException) {
        System.out.println(unwrappedException.getMessage());
      } else {
        throw re;
      }
    } finally {
      cluster.close();
    }
    return exitCode;
  }

  private String getJobPriorityNames() {
    StringBuffer sb = new StringBuffer();
    for (JobPriority p : JobPriority.values()) {
      sb.append(p.name()).append(" ");
    }
    return sb.substring(0, sb.length()-1);
  }

  private String getTaskTypess() {
    StringBuffer sb = new StringBuffer();
    for (TaskType t : TaskType.values()) {
      sb.append(t.name()).append(" ");
    }
    return sb.substring(0, sb.length()-1);
  }

  /**
   * Display usage of the command-line tool and terminate execution.
   */
  private void displayUsage(String cmd) {
    String prefix = "Usage: CLI ";
    String jobPriorityValues = getJobPriorityNames();
    String taskTypes = getTaskTypess();
    String taskStates = "running, completed";
    if ("-submit".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + " <job-file>]");
    } else if ("-status".equals(cmd) || "-kill".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + " <job-id>]");
    } else if ("-counter".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + 
        " <job-id> <group-name> <counter-name>]");
    } else if ("-events".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + 
        " <job-id> <from-event-#> <#-of-events>]. Event #s start from 1.");
    } else if ("-history".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + " <jobHistoryFile>]");
    } else if ("-list".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + " [all]]");
    } else if ("-kill-task".equals(cmd) || "-fail-task".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + " <task-attempt-id>]");
    } else if ("-set-priority".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + " <job-id> <priority>]. " +
          "Valid values for priorities are: " 
          + jobPriorityValues); 
    } else if ("-list-active-trackers".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + "]");
    } else if ("-list-blacklisted-trackers".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + "]");
    } else if ("-list-attempt-ids".equals(cmd)) {
      System.err.println(prefix + "[" + cmd + 
          " <job-id> <task-type> <task-state>]. " +
          "Valid values for <task-type> are " + taskTypes + ". " +
          "Valid values for <task-state> are " + taskStates);
    } else if ("-logs".equals(cmd)) {
      System.err.println(prefix + "[" + cmd +
          " <job-id> <task-attempt-id>]. " +
          " <task-attempt-id> is optional to get task attempt logs.");      
    } else {
      System.err.printf(prefix + "<command> <args>\n");
      System.err.printf("\t[-submit <job-file>]\n");
      System.err.printf("\t[-status <job-id>]\n");
      System.err.printf("\t[-counter <job-id> <group-name> <counter-name>]\n");
      System.err.printf("\t[-kill <job-id>]\n");
      System.err.printf("\t[-set-priority <job-id> <priority>]. " +
        "Valid values for priorities are: " + jobPriorityValues + "\n");
      System.err.printf("\t[-events <job-id> <from-event-#> <#-of-events>]\n");
      System.err.printf("\t[-history <jobHistoryFile>]\n");
      System.err.printf("\t[-list [all]]\n");
      System.err.printf("\t[-list-active-trackers]\n");
      System.err.printf("\t[-list-blacklisted-trackers]\n");
      System.err.println("\t[-list-attempt-ids <job-id> <task-type> " +
        "<task-state>]. " +
        "Valid values for <task-type> are " + taskTypes + ". " +
        "Valid values for <task-state> are " + taskStates);
      System.err.printf("\t[-kill-task <task-attempt-id>]\n");
      System.err.printf("\t[-fail-task <task-attempt-id>]\n");
      System.err.printf("\t[-logs <job-id> <task-attempt-id>]\n\n");
      ToolRunner.printGenericCommandUsage(System.out);
    }
  }
    
  private void viewHistory(String historyFile, boolean all) 
    throws IOException {
    HistoryViewer historyViewer = new HistoryViewer(historyFile,
                                        getConf(), all);
    historyViewer.print();
  }

  protected long getCounter(Counters counters, String counterGroupName,
      String counterName) throws IOException {
    return counters.findCounter(counterGroupName, counterName).getValue();
  }
  
  /**
   * List the events for the given job
   * @param jobId the job id for the job's events to list
   * @throws IOException
   */
  private void listEvents(Job job, int fromEventId, int numEvents)
      throws IOException, InterruptedException {
    TaskCompletionEvent[] events = job.
      getTaskCompletionEvents(fromEventId, numEvents);
    System.out.println("Task completion events for " + job.getJobID());
    System.out.println("Number of events (from " + fromEventId + ") are: " 
      + events.length);
    for(TaskCompletionEvent event: events) {
      System.out.println(event.getStatus() + " " + 
        event.getTaskAttemptId() + " " + 
        getTaskLogURL(event.getTaskAttemptId(), event.getTaskTrackerHttp()));
    }
  }

  protected static String getTaskLogURL(TaskAttemptID taskId, String baseUrl) {
    return (baseUrl + "/tasklog?plaintext=true&attemptid=" + taskId); 
  }
  

  /**
   * Dump a list of currently running jobs
   * @throws IOException
   */
  private void listJobs(Cluster cluster) 
      throws IOException, InterruptedException {
    List<JobStatus> runningJobs = new ArrayList<JobStatus>();
    for (JobStatus job : cluster.getAllJobStatuses()) {
      if (!job.isJobComplete()) {
        runningJobs.add(job);
      }
    }
    displayJobList(runningJobs.toArray(new JobStatus[0]));
  }
    
  /**
   * Dump a list of all jobs submitted.
   * @throws IOException
   */
  private void listAllJobs(Cluster cluster) 
      throws IOException, InterruptedException {
    displayJobList(cluster.getAllJobStatuses());
  }
  
  /**
   * Display the list of active trackers
   */
  private void listActiveTrackers(Cluster cluster) 
      throws IOException, InterruptedException {
    TaskTrackerInfo[] trackers = cluster.getActiveTaskTrackers();
    for (TaskTrackerInfo tracker : trackers) {
      System.out.println(tracker.getTaskTrackerName());
    }
  }

  /**
   * Display the list of blacklisted trackers
   */
  private void listBlacklistedTrackers(Cluster cluster) 
      throws IOException, InterruptedException {
    TaskTrackerInfo[] trackers = cluster.getBlackListedTaskTrackers();
    if (trackers.length > 0) {
      System.out.println("BlackListedNode \t Reason");
    }
    for (TaskTrackerInfo tracker : trackers) {
      System.out.println(tracker.getTaskTrackerName() + "\t" + 
        tracker.getReasonForBlacklist());
    }
  }

  private void printTaskAttempts(TaskReport report) {
    if (report.getCurrentStatus() == TIPStatus.COMPLETE) {
      System.out.println(report.getSuccessfulTaskAttemptId());
    } else if (report.getCurrentStatus() == TIPStatus.RUNNING) {
      for (TaskAttemptID t : 
        report.getRunningTaskAttemptIds()) {
        System.out.println(t);
      }
    }
  }

  /**
   * Display the information about a job's tasks, of a particular type and
   * in a particular state
   * 
   * @param job the job
   * @param type the type of the task (map/reduce/setup/cleanup)
   * @param state the state of the task 
   * (pending/running/completed/failed/killed)
   */
  protected void displayTasks(Job job, String type, String state) 
  throws IOException, InterruptedException {
    TaskReport[] reports = job.getTaskReports(TaskType.valueOf(type));
    for (TaskReport report : reports) {
      TIPStatus status = report.getCurrentStatus();
      if ((state.equals("pending") && status ==TIPStatus.PENDING) ||
          (state.equals("running") && status ==TIPStatus.RUNNING) ||
          (state.equals("completed") && status == TIPStatus.COMPLETE) ||
          (state.equals("failed") && status == TIPStatus.FAILED) ||
          (state.equals("killed") && status == TIPStatus.KILLED)) {
        printTaskAttempts(report);
      }
    }
  }
  
  public void displayJobList(JobStatus[] jobs) 
      throws IOException, InterruptedException {
    System.out.println("Total jobs:" + jobs.length);
    System.out.println("JobId\tState\tStartTime\t" +
        "UserName\tQueue\tPriority\tMaps\tReduces\tUsedContainers\t" +
        "RsvdContainers\tUsedMem\tRsvdMem\tNeededMem\tAM info");
    for (JobStatus job : jobs) {
      TaskReport[] mapReports =
                 cluster.getJob(job.getJobID()).getTaskReports(TaskType.MAP);
      TaskReport[] reduceReports =
                 cluster.getJob(job.getJobID()).getTaskReports(TaskType.REDUCE);

      System.out.printf("%s\t%s\t%d\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%dM\t%dM\t%dM\t%s\n",
          job.getJobID().toString(), job.getState(), job.getStartTime(),
          job.getUsername(), job.getQueue(), 
          job.getPriority().name(),
          mapReports.length,
          reduceReports.length,
          job.getNumUsedSlots(),
          job.getNumReservedSlots(),
          job.getUsedMem(),
          job.getReservedMem(),
          job.getNeededMem(),
          job.getSchedulingInfo());
    }
  }
  
  public static void main(String[] argv) throws Exception {
    int res = ToolRunner.run(new CLI(), argv);
    System.exit(res);
  }
}
