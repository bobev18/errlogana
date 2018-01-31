import re
import os

class TestError():

    def __init__(self, timestamp, userid, cycleid, stepid, errortype, message, test_folder):
        self.cause = ''
        self.time = timestamp
        self.userid = userid
        self.cycleid = cycleid
        self.stepid = stepid
        self.errortype = errortype
        self.message = message
        self.test_folder = test_folder
        # print('ERRORTYPE', self.errortype)
        if errortype == 'Success Validation Failure':
            # sv = re.search(r'step \((.+?)\) was not.+?written to "(.+?)"', message)
            sv = re.search(r'failed sub validations: (.+?)\) for step ".+?" was not found in the response. The response received has been written to "(.+?)"', message)
            # print(sv, type(sv))
            # print(sv, type(sv), sv.groups())
            self.validation = sv.group(1)
            self.file = sv.group(2)

        if errortype == 'Response DD Extraction Failure':
            # ddisrc = re.search(r'response DD item (.+?) used in step (.+?)\.', err)
            ddisrc = re.search(r'Error reading value for response DD item (.+?) used in step .+?', message)
            self.dditem = ddisrc.group(1)
            self.ddi_source = 'gr8' #ddisrc.group(2)    

    def getfile(self):
        if self.errortype == 'Success Validation Failure':
            # print("\nfile:",self.file,self.validation,self.file,'\n')
            try:
                with open(self.test_folder + '/' + self.file) as f:
                    html = f.read()
            except FileNotFoundError:
                # fix folder        --- drops the run-name-folder Performance Test - Test28_09_14_51\
                ## fix_filename = self.file[self.file.find('user'):]
                ## print(self.file, fix_filename)
                ##fix1 = self.file.replace('\\','/')
                ##fix2 = fix1.replace(' ', '\\ ')
                
                drfn = os.path.join(self.test_folder, 'user'+self.userid , self.file)
                ######print(self.test_folder, '|', self.userid, '|', self.file, '|', drfn)
                with open(drfn, 'rt') as f:
                    html = f.read()

        return html

    def determine_casuse(self):
        if self.errortype == 'Success Validation Failure':
            html = self.getfile()
            if html.count('<label for="username">User Name:</label>')>0:
                self.setcause('logged off', '')
                return 'logged off'


            kickoff1 = html.count('<redirect><![CDATA[http://cobmaximo/maximotrain/webclient/login/logout.jsp?timeout=true]]></redirect>') > 0
            kickoff2 = html.count("<![CDATA[warnExit=false; document.location='http://cobmaximo/maximotrain/webclient/login/exit.jsp?sharedSession=1';]]>") > 0
            kickoff3 = html.count("<![CDATA[warnExit=false; document.location='http://cobmaximo/maximosand/webclient/login/exit.jsp?sharedSession=1';]]>") > 0
            kickoff4 = html.count('<redirect><![CDATA[http://cobmaximo/maximosand/webclient/login/logout.jsp]]></redirect>') > 0
            kickoff5 = html.count("<redirect><![CDATA[http://vcobappspr43/maximo/webclient/login/logout.jsp?timeout=true]]></redirect>") > 0
            kickoff6 = html.count("<![CDATA[warnExit=false; document.location='http://vcobappspr43/maximo/webclient/login/exit.jsp?sharedSession=1';]]>") > 0
            if any([kickoff1,kickoff2,kickoff3,kickoff4,kickoff5,kickoff6]):
            # html.count(kickoff1)>0 or html.count(kickoff2)>0 or html.count(kickoff3)>0 or html.count(kickoff4)>0 or html.count(kickoff5)>0 or html.count(kickoff6)>0:
                self.setcause('kicked out', '')
                return 'kicked out'

            if html.count('title="Please wait...">Please wait...</label>')>0:
                self.setcause('Long Op', '')
                return 'Long Op'

            if html.count('MessageWarning.png')>0:
                msg = html[html.find('MessageWarning.png'):]
                msg = '<' + msg[:msg.find('</table>')]
                msg = re.sub(r'<[^>]*?>', '', msg)
                msg = msg.replace('\n','').strip()
                self.setcause('Warning Message', msg)
                return 'Warning Message: ' + msg

            if html.count('st_MessageQuestion.png')>0:
                msg = html[html.find('st_MessageQuestion.png'):]
                msg = '<' + msg[:msg.find('</table>')]
                msg = re.sub(r'<[^>]*?>', '', msg)
                msg = msg.replace('\n','').strip()
                self.setcause('Question Message', msg)
                return 'Question Message: ' + msg
            
            if html.count('st_MessageCritical.png')>0:
                msg = html[html.find('st_MessageCritical.png'):]
                msg = '<' + msg[:msg.find('</table>')]
                msg = re.sub(r'<[^>]*?>', '', msg)
                msg = msg.replace('\n','').strip()
                self.setcause('Critical Message', msg)
                return 'Critical Message: ' + msg

            if html.count('title="0 - 0 of 0">0 - 0 of 0')>0:
                self.setcause('filter zero match', 'searchterm: ' + self.validation)
                return 'filter zero match'

            break_index = html.find('---------------Response-----------------')
            html_request_only = html[:break_index]
            html_response_only = html[break_index + 40:]
            if html_response_only.count(self.validation)>0:
                self.setcause('validation bug', 'searchterm: ' + self.validation)
                return 'validation bug (' + self.file + ')'

            ###  --- COB specific errors ---
            if  html_response_only.count('"id":"0_APPRSS_OPTION","text":"APPRSS"') and not html_response_only.count('Approved'):
                self.setcause('missing "Approved" option', '')
                return 'missing "Approved" option'

            if html_request_only.count('targetId%22%3A%22mx387') and html_response_only.count('title="1 - 2 of 2">1 - 2'):
                self.setcause('dynamic response', 'missing reference of WO field, thus cant validate')
                return 'missing reference of WO field, thus cant validate'

            if html_request_only.count('<command>ISWM-RECORDFAILUREREPORT</command>'):
                self.setcause('response lacks confirmation of recordid', 'response lacks confirmation of recordid')
                return 'response lacks confirmation of recordid'            
            ### --- ==================== ---

            self.setcause('unknown validation fail', html)
            return html
        else:
            self.setcause(self.errortype, '')
            return '!!!!'

    def setcause(self, cause, message):
        self.cause = cause
        self.cause_message = message
