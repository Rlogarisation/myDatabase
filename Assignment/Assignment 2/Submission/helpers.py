# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts 
# you must submit this even if you add nothing
import re

def isGradeCountForWAM(grade):
  if ((grade == "HD" or grade == "DN" or grade == "CR" or grade == "PS") or 
  (grade == "FL" or grade == "AF" or grade == "UF")):
    return True
  else:
    return False

def isGradeCountForUOC(grade):
  if ((grade == "HD" or grade == "DN" or grade == "CR" or grade == "PS") or
  (grade == "XE" or grade == "T") or 
  (grade == "SY" or grade == "EC" or grade == "NC")):
    return True
  else:
    return False

def getOfferbySchool(db, code):
  cur = db.cursor()
  cur.execute("select * from orgunits where id = %s",[code])
  info = cur.fetchone()
  cur.close()
  if not info:
    return None
  else:
    return info

def getRecentEnrolledProgramIdByStuId(db,studentId):
  cur = db.cursor()
  qry = """
  select pe.program
  from program_enrolments pe
  where pe.student = %s
  order by pe.term
  """
  cur.execute(qry,[studentId])
  programId = cur.fetchone()
  cur.close()
  if not programId:
    return None
  else:
    return programId

def getProgram(db,code):
  cur = db.cursor()
  cur.execute("select * from Programs where id = %s",[code])
  info = cur.fetchone()
  cur.close()
  if not info:
    return None
  else:
    return info

def getRecentEnrolledProgramStreamByStuId(db,studentId):
  cur = db.cursor()
  qry = """
  select pe.program, s.code
  from program_enrolments pe
  join stream_enrolments se on se.partof = pe.id
  join streams s on se.stream = s.id
  where pe.student = %s
  order by pe.term
  """
  cur.execute(qry,[studentId])
  programStream = cur.fetchone()
  cur.close()
  if not programStream:
    return None
  else:
    return programStream

def getStream(db,code):
  cur = db.cursor()
  cur.execute("select * from Streams where code = %s",[code])
  info = cur.fetchone()
  cur.close()
  if not info:
    return None
  else:
    return info

def getCourse(db, courseCode):
  cur = db.cursor()
  cur.execute("select * from subjects where code = %s",[courseCode])
  info = cur.fetchone()
  cur.close()
  if not info:
    return None
  else:
    return info

def getStudent(db,zid):
  cur = db.cursor()
  qry = """
  select p.*, c.name
  from   People p
         join Students s on s.id = p.id
         join Countries c on p.origin = c.id
  where  p.id = %s
  """
  cur.execute(qry,[zid])
  info = cur.fetchone()
  cur.close()
  if not info:
    return None
  else:
    return info

def getTranscript(db,zid):
  cur = db.cursor()
  cur.execute("select * from transcript(%s)",[zid])
  info = cur.fetchall()
  cur.close()
  res = ""
  if not info:
    return None
  else:

    totalUocforWAM = 0
    totalUoc = 0
    sumOfProduct = 0
    for eachCourse in info:
      (courseCode, term, courseTitle, mark, grade, uoc) = eachCourse

      if mark == 0:
        markForPrint = "-"
      else:
        markForPrint = mark
      # UOC printing guidance:
      # Xuoc for A,B,C,D,HD,DN,CR.PS,XE,T,SY,EC,NC
      # fail for AF,FL,UF
      # nothing for AS,AW,PW,RD,NF,LE,PE,WD,WJ
      if grade == "FL" or grade == "UF" or grade == "AF":
        uocForPrint = " fail"
      elif (grade == "AS" or grade == "AW" or grade == "PW" or grade == "RD" or 
      grade == "NF" or grade == "LE" or grade == "PE" or
      grade == "WD" or grade == "WJ"):
        uocForPrint = ""
      else:
        uocForPrint = f"{uoc:2d}uoc"

      markString = "{:>3}"
      res += f"{courseCode} {term} {courseTitle:<32s}{markString.format(markForPrint)} {grade:>2s}  {uocForPrint}\n"
      if isGradeCountForWAM(grade):
        totalUocforWAM += uoc
        sumOfProduct += mark * uoc
      if isGradeCountForUOC(grade):
        totalUoc += uoc
    averageWAM = sumOfProduct / totalUocforWAM
    oneDecimal = "{:.1f}"
    res += f"UOC = {totalUoc}, WAM = {oneDecimal.format(averageWAM)}"
  return res

def getTranscriptForProgression(db, zid, rulesInfo):
  cur = db.cursor()
  cur.execute("select * from transcript(%s)",[zid])
  info = cur.fetchall()
  cur.close()
  res = ""
  if not info:
    return None
  else:
    res += "Completed:\n"
    totalUocforWAM = 0
    # Create an individual dictionary to store uoc information.
    # groupName minimumUoc maximumUoc currentUoc
    currentUocTable = []
    for rules in rulesInfo:
      (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = rules
      foundItem = 0
      for items in currentUocTable:
        if eachName in items['name']:
          foundItem = 1
      if foundItem == 0:
        newDic = {
            "name": eachName,
            "minUoc": eachMin,
            "maxUoc": eachMax,
            "currentUoc": 0
          }
        currentUocTable.append(newDic)
    
    
    # Check information for each course in the transcript
    for eachCourse in info:
      isNotSatisfy = 0
      rulesForPrint = ""
      (courseCode, term, courseTitle, mark, grade, uoc) = eachCourse
      
      # Check the current course by looping through all the rules info.
      if grade == "FL":
        rulesForPrint = "does not count"
      else:
        for eachRule in rulesInfo:
          (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachRule
          if courseCode in eachCourse and eachName != "ADK Courses":
            if (eachMax is not None and checkCurrentUoc(eachName, currentUocTable) < eachMax) or eachMax is None:
              rulesForPrint = f"towards {eachName}"
              currentUocTable = increaseCurrentUoc(eachName, 6, currentUocTable)
              rulesInfo.remove(eachRule)
              if courseIsADK(courseCode, rulesInfo):
                  rulesForPrint += " + ADK Courses"
                  currentUocTable = increaseCurrentUoc("ADK Courses", 6, currentUocTable)
              

        if rulesForPrint == "":
          for eachRule in rulesInfo:
            (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachRule
            if "#" in eachCourse and courseCode[0:5] == eachCourse[0:5]:
              if (eachMax is not None and checkCurrentUoc(eachName, currentUocTable) < eachMax) or eachMax is None:
                rulesForPrint = f"towards {eachName}"
                currentUocTable = increaseCurrentUoc(eachName, 6, currentUocTable)
                if courseIsADK(courseCode, rulesInfo):
                  rulesForPrint += " + ADK Courses"
                  currentUocTable = increaseCurrentUoc("ADK Courses", 6, currentUocTable)

        if rulesForPrint == "":
          for eachRule in rulesInfo:
            (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachRule
            if "#" in eachCourse and "FREE" in eachCourse:
              if (eachMax is not None and checkCurrentUoc(eachName, currentUocTable) < eachMax) or eachMax is None:
                rulesForPrint = "towards Free Electives"
                currentUocTable = increaseCurrentUoc(eachName, 6, currentUocTable)
              

        if rulesForPrint == "":
          rulesForPrint = "does not satisfy any rule"
          isNotSatisfy = 1

      if mark == 0:
        markForPrint = "-"
      else:
        markForPrint = mark
      # UOC printing guidance:
      # Xuoc for A,B,C,D,HD,DN,CR.PS,XE,T,SY,EC,NC
      # fail for AF,FL,UF
      # nothing for AS,AW,PW,RD,NF,LE,PE,WD,WJ
      if grade == "FL" or grade == "UF" or grade == "AF":
        uocForPrint = " fail"
      elif (grade == "AS" or grade == "AW" or grade == "PW" or grade == "RD" or 
      grade == "NF" or grade == "LE" or grade == "PE" or
      grade == "WD" or grade == "WJ") or isNotSatisfy:
        uocForPrint = " 0uoc"
      elif isNotSatisfy == 0:
        uocForPrint = f"{uoc:2d}uoc"
        totalUocforWAM += uoc

      markString = "{:>3}"
      res += f"{courseCode} {term} {courseTitle:<32s}{markString.format(markForPrint)} {grade:>2s}  {uocForPrint} {rulesForPrint}\n"
    res += f"UOC = {totalUocforWAM} so far\n"
    res += "\n"
    if isCompleteDegree(rulesInfo, currentUocTable):
      res += "Eligible to graduate\n"
    else:
      res += "Remaining to complete degree:\n"
      # Display all the cc course first
      for eachCourse in rulesInfo:
        (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachCourse
        if eachGradeType == "CC" and not re.search("^{.*}$", eachCourse):
          res += f"- {eachCourse} {getCourse(db, eachCourse)[2]}\n"
        elif eachGradeType == "CC" and re.search("^{.*}$", eachCourse):
          eachCourse = eachCourse.replace('{', '', 1)
          eachCourse = eachCourse.replace('}', '', 1)
          counter = 0
          for multiCourse in eachCourse.split(";"):
            courseInfo = getCourse(db,multiCourse)
            if not courseInfo:
              coursePrintInfo = "???"
            else:
              coursePrintInfo = courseInfo[2]
            if counter == 0:
              res += f"- {multiCourse} {coursePrintInfo}\n"
            else:
              res += f"  or {multiCourse} {coursePrintInfo}\n"
            counter += 1
      # Then display all the PE's
      for eachCourse in rulesInfo:
        (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachCourse
        # Find out how many uoc need to be done.
        uocDone = checkCurrentUoc(eachName, currentUocTable)
        if eachGradeType == "PE" and not eachName == "ADK Courses":
          if eachMin is None and eachMax - uocDone > 0:
            res += f"up to {eachMax - uocDone} UOC courses from {eachName}\n"
          elif eachMax is None and eachMin - uocDone > 0:
            res += f"at least {eachMin - uocDone} UOC courses from {eachName}\n"
          elif eachMax == eachMin and eachMin - uocDone > 0:
            res += f"{eachMin - uocDone} UOC courses from {eachName}\n"
          elif eachMin is not None and eachMax is not None and eachMin < eachMax and eachMin - uocDone >= 0:
            res += f"between {eachMin - uocDone} and {eachMax - uocDone} UOC courses from {eachName}\n"
          break
      for eachCourse in rulesInfo:
        (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachCourse
        # Find out how many uoc need to be done.
        uocDone = checkCurrentUoc(eachName, currentUocTable)
        if eachGradeType == "PE" and eachName == "ADK Courses":
          if eachMin is None and eachMax - uocDone > 0:
            res += f"up to {eachMax - uocDone} UOC from {eachName}\n"
          elif eachMax is None and eachMin - uocDone > 0:
            res += f"at least {eachMin - uocDone} UOC from {eachName}\n"
          elif eachMax == eachMin and eachMin - uocDone > 0:
            res += f"{eachMin - uocDone} UOC from {eachName}\n"
          elif eachMin is not None and eachMax is not None and eachMin < eachMax and eachMin - uocDone >= 0:
            res += f"between {eachMin - uocDone} and {eachMax - uocDone} UOC from {eachName}\n"
          break
      # Then do GE
      for eachCourse in rulesInfo:
        (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachCourse
        uocDone = checkCurrentUoc(eachName, currentUocTable)
        if eachGradeType == "GE" and eachMin - uocDone > 0:
          if eachMin == eachMax and eachMax is not None:
            res += f"{eachMin - uocDone} UOC of General Education\n"
            break
      # Eventually FE
      for eachCourse in rulesInfo:
        (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachCourse
        uocDone = checkCurrentUoc(eachName, currentUocTable)
        if eachGradeType == "FE":
          if eachMin is None and eachMax - uocDone > 0:
            res += f"up to {eachMax - uocDone} UOC of Free Electives\n"
          elif eachMax is None and eachMin - uocDone > 0:
            res += f"at least {eachMin - uocDone} UOC of Free Electives\n"
          elif eachMax == eachMin and eachMin - uocDone > 0:
            res += f"{eachMin - uocDone} UOC of Free Electives\n"
          elif eachMin is not None and eachMax is not None and eachMin < eachMax and eachMin - uocDone >= 0:
            res += f"between {eachMin - uocDone} and {eachMax - uocDone} UOC of Free Electives\n"
          break
  return res

def getRulesForProgram(db, programId, forPrint):
  cur = db.cursor()
  qry = """
  select r.name, r.type, r.min_req, r.max_req, aog.type, aog.defby, aog.definition
  from rules r
  join program_rules pr on r.id = pr.rule
  join programs p on p.id = pr.program
  join academic_object_groups aog on r.ao_group = aog.id
  where pr.program = %s
  """
  cur.execute(qry,[programId])
  info = cur.fetchall()
  cur.close()
  if forPrint == 0:
    return rulesResult(db, info)
  else:
    return info
  


def getRulesForStream(db, streamId, forPrint):
  cur = db.cursor()
  qry = """
  select r.name, r.type, r.min_req, r.max_req, aog.type, aog.defby, aog.definition
  from streams s
  join stream_rules sr on s.id = sr.stream
  join rules r on sr.rule = r.id
  join academic_object_groups aog on r.ao_group = aog.id
  where s.id = %s
  """
  cur.execute(qry,[streamId])
  info = cur.fetchall()
  cur.close()
  if forPrint == 0:
    return rulesResult(db, info)
  else:
    return info

def rulesResult(db, info):
  res = ""
  if not info:
    return None
  else:
    for each in info: 
      typeMsg = ""
      reqMsg = "" 
      # print(each)                   
      (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachDef) = each
      # # Determine the each type.
      if eachType == "stream":
        typeMsg = " stream(s) from "
      elif eachType == "subject":
        typeMsg = " courses from " 

      # TODO: This can be separated into single function.
      # TODO: Didn't use the grade type of 'WM', might need more case to test it.
      # Determine the requirement number.
      if eachGradeType == 'CC':
        if len(eachDef.split(",")) > 1:
          reqMsg = "all"
        elif len(eachDef.split(",")) == 1:
          reqMsg = ""
          typeMsg = ""
      elif eachGradeType == 'DS':
        if eachMin == eachMax and eachMin is not None:
          reqMsg = eachMin
      elif eachGradeType == 'PE' or eachGradeType == 'FE':
        if eachMin is None:
          reqMsg = f"up to {eachMax} UOC"
        elif eachMax is None:
          reqMsg = f"at least {eachMin} UOC"
        elif eachMax == eachMin:
          reqMsg = f"{eachMin} UOC"
        elif eachMin < eachMax:
          reqMsg = f"between {eachMin} and {eachMax} UOC"
      elif eachGradeType == 'GE':
        if eachMin == eachMax and eachMax is not None:
          reqMsg = f"{eachMin} UOC"
      
      # Special Types
      if eachGradeType == 'FE':
        typeMsg = " of "
        eachName = "Free Electives"
        res += f"{reqMsg}{typeMsg}{eachName}\n"
      elif eachGradeType == 'GE':
        typeMsg = " of "
        eachName = "General Education"
        res += f"{reqMsg}{typeMsg}{eachName}"
      else:
        res += f"{reqMsg}{typeMsg}{eachName}\n"
      # Enumerated style
      if eachDefby == 'enumerated':
        for course in eachDef.split(","):
          # Stream Situation
          if len(course) == 6:
            streamInfo = getStream(db, course)
            if not streamInfo:
              streamInfoPrint = "???"
            else:
              streamInfoPrint = streamInfo[2]
            res += f"- {course} {streamInfoPrint}\n"
          # Course situation
          elif len(course) == 8:
            courseInfo = getCourse(db,course)
            if not courseInfo:
              courseInfoPrint = "???"
            else:
              courseInfoPrint = courseInfo[2]
            res += f"- {course} {courseInfoPrint}\n"

          # Need to consider the pattern for {} 
          elif re.search("^{.*}$", course):
            course = course.replace('{', '', 1)
            course = course.replace('}', '', 1)
            counter = 0
            for multiCourse in course.split(";"):
              courseInfo = getCourse(db,multiCourse)
              if not courseInfo:
                coursePrintInfo = "???"
              else:
                coursePrintInfo = courseInfo[2]
              if counter == 0:
                res += f"- {multiCourse} {coursePrintInfo}\n"
              else:
                res += f"  or {multiCourse} {coursePrintInfo}\n"
              counter += 1
          # else:
          #   res += ""
      elif eachDefby == 'pattern' and ((not eachGradeType == 'FE') and (not eachGradeType == 'GE')):
        res += f"- courses matching {eachDef}\n"
    return res


def arrangeStreamProgramInfos(progInfo, StreamInfo):
  result = []
  
  for eachProg in progInfo:
    (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachDef) = eachProg
    for eachCourse in eachDef.split(","):
      result.append([eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse])

  for eachStream in StreamInfo:
    (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachDef) = eachStream
    if eachType != "stream":
      for eachCourse in eachDef.split(","):
        result.append([eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse])

  return result


def checkCurrentUoc(nameGroup, currentUocTable):
  for item in currentUocTable:
    if nameGroup == item['name']:
      return item['currentUoc']
  return 99

def increaseCurrentUoc(nameGroup, increment, currentUocTable):
  for item in currentUocTable:
    if nameGroup == item['name']:
      item['currentUoc'] += increment
      break
  return currentUocTable
  
def courseIsADK(courseCode, rulesInfo):
  for eachRule in rulesInfo:
    (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachRule
    if courseCode in eachCourse and eachName == "ADK Courses":
      return True
  return False

def isCompleteDegree(rulesInfo, currentUocTable):
  for eachCourse in rulesInfo:
    (eachName, eachGradeType, eachMin, eachMax, eachType, eachDefby, eachCourse) = eachCourse
    if eachGradeType == "CC":
      return False
    uocDone = checkCurrentUoc(eachName, currentUocTable)
    if eachGradeType == "PE":
      if eachMin is None and eachMax - uocDone > 0:
        return False
      elif eachMax is None and eachMin - uocDone > 0:
        return False
      elif eachMax == eachMin and eachMin - uocDone > 0:
        return False
      elif eachMin is not None and eachMax is not None and eachMin < eachMax and eachMin - uocDone >= 0:
        return False
    if eachGradeType == "GE" and eachMin - uocDone > 0:
        if eachMin == eachMax and eachMax is not None:
          return False
    if eachGradeType == "FE":
        if eachMin is None and eachMax - uocDone > 0:
          return False
        elif eachMax is None and eachMin - uocDone > 0:
          return False
        elif eachMax == eachMin and eachMin - uocDone > 0:
          return False
        elif eachMin is not None and eachMax is not None and eachMin < eachMax and eachMin - uocDone >= 0:
          return False
  return True