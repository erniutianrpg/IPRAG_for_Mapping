package org.bigbluebutton.core.models

import com.softwaremill.quicklens._
import org.bigbluebutton.core.db.{ UserDAO, UserVoiceDAO }

object VoiceUsers {
  def findWithVoiceUserId(users: VoiceUsers, voiceUserId: String): Option[VoiceUserState] = {
    users.toVector find (u => u.voiceUserId == voiceUserId)
  }

  def findWIthIntId(users: VoiceUsers, intId: String): Option[VoiceUserState] = {
    users.toVector.find(u => u.intId == intId)
  }

  def findAll(users: VoiceUsers): Vector[VoiceUserState] = users.toVector

  def findAllNonListenOnlyVoiceUsers(users: VoiceUsers): Vector[VoiceUserState] = users.toVector.filter(u => u.listenOnly == false)
  def findAllListenOnlyVoiceUsers(users: VoiceUsers): Vector[VoiceUserState] = users.toVector.filter(u => u.listenOnly == true)
  def findAllFreeswitchCallers(users: VoiceUsers): Vector[VoiceUserState] = users.toVector.filter(u => u.calledInto == "freeswitch")
  def findAllKurentoCallers(users: VoiceUsers): Vector[VoiceUserState] = users.toVector.filter(u => u.calledInto == "kms")

  def findAllBannedCallers(users: VoiceUsers): Vector[VoiceUserState] = users.bannedUsers.values.toVector

  def isCallerBanned(callerIdNum: String, users: VoiceUsers): Boolean = {
    users.bannedUsers.contains(callerIdNum)
  }

  def ban(users: VoiceUsers, user: VoiceUserState): Unit = {
    users.ban(user)
  }

  def add(users: VoiceUsers, user: VoiceUserState): Unit = {
    users.save(user)
    UserVoiceDAO.insert(user)
  }

  def removeWithIntId(users: VoiceUsers, intId: String): Option[VoiceUserState] = {
    UserVoiceDAO.deleteUser(intId)
    users.remove(intId)
  }

  def findWithIntId(users: VoiceUsers, intId: String): Option[VoiceUserState] = {
    users.toVector.find(u => u.intId == intId)
  }

  def recoverVoiceUser(users: VoiceUsers, intId: String): Option[VoiceUserState] = {
    users.removeFromCache(intId)
  }

  def userMuted(users: VoiceUsers, voiceUserId: String, muted: Boolean): Option[VoiceUserState] = {
    for {
      u <- findWithVoiceUserId(users, voiceUserId)
    } yield {
      val vu = u.modify(_.muted).setTo(muted)
        .modify(_.talking).setTo(false)
        .modify(_.lastStatusUpdateOn).setTo(System.currentTimeMillis())
      users.save(vu)
      UserVoiceDAO.update(vu)
      UserVoiceDAO.updateTalking(vu)
      vu
    }
  }

  def userTalking(users: VoiceUsers, voiceUserId: String, talking: Boolean): Option[VoiceUserState] = {
    for {
      u <- findWithVoiceUserId(users, voiceUserId)
    } yield {
      val vu = u.modify(_.muted).setTo(false)
        .modify(_.talking).setTo(talking)
        .modify(_.lastStatusUpdateOn).setTo(System.currentTimeMillis())
      users.save(vu)
      UserVoiceDAO.updateTalking(vu)

      vu
    }
  }

  def becameFloor(users: VoiceUsers, voiceUserId: String, floor: Boolean, timestamp: String): Option[VoiceUserState] = {
    for {
      u <- findWithVoiceUserId(users, voiceUserId)
    } yield {
      val vu = u.modify(_.floor).setTo(floor)
        .modify(_.lastFloorTime).setTo(timestamp)
        .modify(_.lastStatusUpdateOn).setTo(System.currentTimeMillis())
      users.save(vu)
      UserVoiceDAO.update(vu)
      vu
    }
  }

  def releasedFloor(users: VoiceUsers, voiceUserId: String, floor: Boolean): Option[VoiceUserState] = {
    for {
      u <- findWithVoiceUserId(users, voiceUserId)
    } yield {
      val vu = u.modify(_.floor).setTo(floor)
        .modify(_.lastStatusUpdateOn).setTo(System.currentTimeMillis())
      users.save(vu)
      UserVoiceDAO.update(vu)
      vu
    }
  }

  def setLastStatusUpdate(users: VoiceUsers, user: VoiceUserState): VoiceUserState = {
    val vu = user.copy(lastStatusUpdateOn = System.currentTimeMillis())
    users.save(vu)
    vu
  }
}

class VoiceUsers {
  private var users: collection.immutable.HashMap[String, VoiceUserState] = new collection.immutable.HashMap[String, VoiceUserState]

  // Keep track of ejected voice users to prevent them from rejoining.
  // ralam april 23, 2020
  private var bannedUsers: collection.immutable.HashMap[String, VoiceUserState] = new collection.immutable.HashMap[String, VoiceUserState]

  // Collection of users that left the meeting. We keep a cache of the old users state to recover in case
  // the user reconnected by refreshing the client. (ralam june 13, 2017)
  private var usersCache: collection.immutable.HashMap[String, VoiceUserState] = new collection.immutable.HashMap[String, VoiceUserState]

  private def toVector: Vector[VoiceUserState] = users.values.toVector

  private def ban(user: VoiceUserState): VoiceUserState = {
    bannedUsers += user.callerNum -> user
    user
  }

  private def save(user: VoiceUserState): VoiceUserState = {
    users += user.intId -> user
    user
  }

  private def remove(intId: String): Option[VoiceUserState] = {
    for {
      user <- users.get(intId)
    } yield {
      users -= intId
      saveToCache(user)
      user
    }
  }

  private def saveToCache(
      user: VoiceUserState
  ): Unit = {
    usersCache += user.intId -> user
  }

  private def removeFromCache(
      intId: String
  ): Option[VoiceUserState] = {
    for {
      user <- usersCache.get(intId)
    } yield {
      usersCache -= intId
      user
    }
  }
}

case class VoiceUser2x(
    intId:       String,
    voiceUserId: String
)
case class VoiceUserVO2x(
    intId:         String,
    voiceUserId:   String,
    callerName:    String,
    callerNum:     String,
    joined:        Boolean,
    locked:        Boolean,
    muted:         Boolean,
    talking:       Boolean,
    callingWith:   String,
    listenOnly:    Boolean,
    floor:         Boolean,
    lastFloorTime: String
)

case class VoiceUserState(
    intId:              String,
    voiceUserId:        String,
    callingWith:        String,
    callerName:         String,
    callerNum:          String,
    color:              String,
    muted:              Boolean,
    talking:            Boolean,
    listenOnly:         Boolean,
    calledInto:         String,
    lastStatusUpdateOn: Long,
    floor:              Boolean,
    lastFloorTime:      String
)
