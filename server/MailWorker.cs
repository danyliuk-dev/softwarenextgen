using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.DataProtection;
using Npgsql;
sealed class MailWorker(Store db,IConfiguration config,IHttpClientFactory clients,IDataProtectionProvider protection,ILogger<MailWorker> log):BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stop)
    {
        while(!stop.IsCancellationRequested){try{if(config["Mail:Enabled"]=="true")for(int i=0;i<10;i++)if(!await Send(stop))break;}catch(OperationCanceledException)when(stop.IsCancellationRequested){break;}catch(Exception ex){log.LogWarning("Mail processing failed: {Type}",ex.GetType().Name);}try{await Task.Delay(TimeSpan.FromSeconds(20),stop);}catch(OperationCanceledException){break;}}
    }
    async Task<bool> Send(CancellationToken ct)
    {
        await using var conn=await db.Source.OpenConnectionAsync(ct);await using var tx=await conn.BeginTransactionAsync(ct);
        await using var cmd=new NpgsqlCommand("SELECT m.id,m.recipient,m.payload,m.attempts,i.used_at IS NULL AND i.expires_at>now() AND u.enabled FROM mail_outbox m JOIN invitations i ON i.id=m.invitation_id JOIN users u ON u.id=i.user_id WHERE m.status='pending' AND m.next_attempt<=now() ORDER BY m.next_attempt FOR UPDATE OF m SKIP LOCKED LIMIT 1",conn,tx);
        object[] row;await using(var r=await cmd.ExecuteReaderAsync(ct)){if(!await r.ReadAsync(ct))return false;row=new object[r.FieldCount];r.GetValues(row);}
        var status=(bool)row[4]?"pending":"cancelled";var error="";var attempts=(int)row[3]+1;
        if(status=="pending")try{
            var token=Encoding.UTF8.GetString(protection.CreateProtector("Nextgen.AccountSecrets.v1").Unprotect(Convert.FromBase64String((string)row[2])));
            error=await PortalMail.Send(clients,config,(string)row[1],"Set up your Software Next Generation password","Open this link to set your Software Next Generation password:\nhttps://softwarenextgen.com/accept#"+token+"\n\nThis personal link expires in 48 hours and can be used only once. If you did not request or expect this email, ignore this email.\n\nSoftware Next Generation",ct);
            if(error=="")status="accepted";
        }catch(OperationCanceledException)when(ct.IsCancellationRequested){throw;}catch(Exception){error="Mail connection failed; delivery uncertain";}
        if(status=="pending"&&attempts>=8)status="failed";
        await using var update=new NpgsqlCommand("UPDATE mail_outbox SET status=$2,attempts=$3,error=$4,next_attempt=now()+($5*interval '1 minute'),accepted_at=CASE WHEN $2='accepted' THEN now() ELSE NULL END,payload=CASE WHEN $2 IN ('accepted','cancelled','failed') THEN '' ELSE payload END WHERE id=$1",conn,tx);
        foreach(var v in new object[]{row[0],status,attempts,error,Math.Min(360,(int)Math.Pow(2,attempts))})update.Parameters.AddWithValue(v);
        await update.ExecuteNonQueryAsync(ct);await tx.CommitAsync(ct);return true;
    }
}
