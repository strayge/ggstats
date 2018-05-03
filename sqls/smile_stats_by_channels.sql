SELECT count(*) AS count, ggchat_user.username
FROM ggchat_message
  LEFT OUTER JOIN ggchat_channel ON ggchat_message.channel_id = ggchat_channel.channel_id
  LEFT OUTER JOIN ggchat_user ON ggchat_channel.streamer_id = ggchat_user.user_id
WHERE ggchat_message.text LIKE '%:drake:%'
      and ggchat_message.timestamp > '2018-04-01'
      and ggchat_message.timestamp < '2018-05-01'
group by ggchat_message.channel_id
order by count desc