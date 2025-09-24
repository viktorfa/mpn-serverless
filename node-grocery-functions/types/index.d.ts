export interface SnsRecord<Message> {
  Sns: { Message: Message };
}

export interface SnsEvent<Message> {
  Records: { 0: SnsRecord<Message> };
}
