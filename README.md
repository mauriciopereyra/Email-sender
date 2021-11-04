# Email sender
Django script to automatically send emails daily to a mailing list

<h2>Features</h2>

* Connected to Mailgun API for sending emails
* Connected to EmailListVerify API for checking that email addresses are active (1)
* Sending emails daily or one time. Can specify how many emails to send.
* If sending daily, the number of emails sent per day will gradually increase up to 100 emails per day (2)
* Scheduling to a specific time
* Keeping track of how many emails were sent to each contact
* Filtering out contacts who have unsuscribed from the list
* Checking each email sent. If status is failed, no more emails will be sent to that contact.
* Emails will be sent with random intervals (3)

<h3>Notes</h3>

* (1) To avoid emails bounces.
* (2) This is a good practice for a new email address. 
* (3) The interval can be specified, but this script will make it vary a few minutes so it is not the same interval always.
<p>All these are meant to protect sender reputation and avoid being marked as spam.</p>
