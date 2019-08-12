# Copyright (c) 2019 FLOW Executive Finders
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime
from pprint import pprint

from pyhorn import auth, client

credentials = auth.Credentials.from_json("auth.json")
client.set_logger_level("DEBUG")


def get_latest_five_companies():
    entity = "ClientCorporation"
    query = "(status:Cliente* OR status:Prospect)"
    fields = ",".join([
        "id", "externalID", "name", "customText2", "status",
        "businessSectorList", "industryList", "dateAdded"
    ])
    with client.RESTClient(credentials) as bullhorn:
        response = bullhorn.search(entity,
                                   query,
                                   fields=fields,
                                   sort="-dateAdded",
                                   count=5)
        batch = response["data"]
        print(response)
        for record in batch:
            timestamp = float(record["dateAdded"]) / 1000.0

            formatted = {
                "nome": record["name"],
                "bullhornId": record["id"],
                "profileId": record["externalID"],
                "proprietario": record["customText2"],
                "status": record["status"],
                "mercadoMacro": record["businessSectorList"],
                "mercadoMicro": ", ".join(record["industryList"] or []),
                "criadoEm": datetime.fromtimestamp(timestamp)
            }

            pprint(formatted)
        return response


def get_categories():
    entity = "Category"
    fields = "id,enabled,dateAdded,description,name,occupation,type"
    where = "enabled = TRUE"
    with client.RESTClient(credentials) as bullhorn:
        response = bullhorn.query(entity,
                                  where,
                                  fields=fields,
                                  sort="-dateAdded",
                                  meta="basic")
        batch = response["data"]
        print(response)
        print(f"Batch returned {len(batch)} records.")
        for record in batch:
            record["dateAdded"] = datetime.fromtimestamp(
                float(record["dateAdded"]) / 1000.0)
            pprint(record)


def get_company(entityId):
    entity = "ClientCorporation"
    fields = "name,status,businessSectorList,industryList"

    with client.RESTClient(credentials) as bullhorn:
        data = bullhorn.get_entity(entity, entityId, fields=fields)
        print(data)


def get_company_contacts(company_ids):
    entity = "ClientCorporation"
    fields = "address,clientCorporation"

    with client.RESTClient(credentials) as bullhorn:
        data = bullhorn.get_tomany(entity,
                                   company_ids,
                                   "clientContacts",
                                   fields=fields,
                                   count=5)
        return data


def test_ping():
    with client.RESTClient(credentials) as bullhorn:
        print(bullhorn.ping())


with client.RESTClient(credentials) as bullhorn:
    job_order = bullhorn.capture("test-sub")
    pprint(job_order)
